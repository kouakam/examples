"""Cas 5 · Chaîne d'approvisionnement — outils de l'agent de réapprovisionnement.

La prévision de la demande est un modèle statistique classique (régression
linéaire sur 12 semaines) exposé comme un outil : le LLM ne prévoit pas les
séries temporelles, il orchestre, croise avec des signaux non structurés
(courriels, CRM, actualité) et justifie ses propositions.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from noyau import ErreurOutil, Outil

DOSSIER = Path(__file__).parent / "donnees"
SEUIL_VALIDATION_FCFA = 500_000
SEMAINES_COUVERTURE_CIBLE = 4


def _charger(nom: str):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


def _regression(valeurs: list[float]) -> tuple[float, float]:
    n = len(valeurs)
    xs = range(1, n + 1)
    mx, my = sum(xs) / n, sum(valeurs) / n
    pente = sum((x - mx) * (y - my) for x, y in zip(xs, valeurs)) / sum((x - mx) ** 2 for x in xs)
    return pente, my - pente * mx


class Etat:
    def __init__(self):
        self.articles = {a["sku"]: a for a in _charger("articles.json")}
        self.offres = _charger("offres_fournisseurs.json")
        self.en_cours = _charger("commandes_en_cours.json")
        self.signaux = _charger("signaux.json")
        self.ventes: dict[str, list[int]] = {}
        with (DOSSIER / "ventes_hebdomadaires.csv").open(encoding="utf-8") as f:
            for ligne in csv.DictReader(f):
                self.ventes.setdefault(ligne["sku"], []).append(int(ligne["quantite"]))
        self.demandes_achat: list[dict] = []
        self.alertes: list[dict] = []

    def _article(self, sku: str) -> dict:
        if sku not in self.articles:
            raise ErreurOutil(f"Article {sku} inconnu.")
        return self.articles[sku]

    # --------------------------------------------------------------- analyse
    def prevision_demande(self, sku: str, horizon_jours: int) -> dict:
        self._article(sku)
        historique = self.ventes[sku]
        pente, origine = _regression(historique)
        hebdo = max(0.0, origine + pente * (len(historique) + 1))
        residus = [y - (origine + pente * x) for x, y in enumerate(historique, 1)]
        ecart_type = math.sqrt(sum(r * r for r in residus) / max(1, len(residus) - 2))
        semaines = horizon_jours / 7
        return {"sku": sku, "horizon_jours": horizon_jours, "demande_hebdo_prevue": round(hebdo, 1),
                "tendance_hebdo": round(pente, 2), "demande_horizon": math.ceil(hebdo * semaines),
                "intervalle_95": [max(0, math.floor((hebdo - 1.96 * ecart_type) * semaines)),
                                  math.ceil((hebdo + 1.96 * ecart_type) * semaines)],
                "methode": "régression linéaire sur 12 semaines"}

    def analyser_stocks(self) -> list[dict]:
        resultat = []
        for sku, a in self.articles.items():
            hebdo = self.prevision_demande(sku, 7)["demande_hebdo_prevue"]
            en_commande = sum(c["quantite"] for c in self.en_cours if c["sku"] == sku)
            couverture = round((a["stock"] + en_commande) / hebdo * 7) if hebdo else None
            resultat.append({"sku": sku, "designation": a["designation"], "stock": a["stock"],
                             "stock_securite": a["stock_securite"], "en_commande": en_commande,
                             "demande_hebdo_prevue": hebdo, "couverture_jours": couverture})
        return resultat

    def comparer_fournisseurs(self, sku: str) -> list[dict]:
        self._article(sku)
        return [o for o in self.offres if o["sku"] == sku]

    def lire_signaux(self) -> list[dict]:
        return self.signaux

    # --------------------------------------------------------------- actions
    def creer_demande_achat(self, sku: str, fournisseur: str, quantite: int, justification: str) -> dict:
        offre = next((o for o in self.offres if o["sku"] == sku and o["fournisseur"] == fournisseur), None)
        if offre is None:
            raise ErreurOutil(f"Aucune offre de « {fournisseur} » pour {sku}.")
        if quantite < offre["minimum"]:
            raise ErreurOutil(f"Quantité inférieure au minimum de commande ({offre['minimum']}).")
        montant = quantite * offre["prix_unitaire"]
        validation = montant > SEUIL_VALIDATION_FCFA or not offre["reference"]
        demande = {"reference": f"DA-{700 + len(self.demandes_achat)}", "sku": sku, "fournisseur": fournisseur,
                   "quantite": quantite, "montant_fcfa": montant, "justification": justification,
                   "statut": "en attente de validation de l'acheteur" if validation else "émise au fournisseur"}
        self.demandes_achat.append(demande)
        return demande

    def alerter_acheteur(self, sku: str, niveau: str, message: str) -> dict:
        self.alertes.append({"sku": sku, "niveau": niveau, "message": message})
        return {"statut": "alerte envoyée", "niveau": niveau}

    def bilan(self) -> dict:
        return {"demandes_achat": self.demandes_achat, "alertes": self.alertes}


def construire_outils(e: Etat) -> list[Outil]:
    t, entier = {"type": "string"}, {"type": "integer"}
    return [
        Outil("analyser_stocks", "Vue d'ensemble : stock, stock de sécurité, quantités en commande, demande "
              "hebdomadaire prévue et couverture en jours pour chaque article.", {}, e.analyser_stocks),
        Outil("prevision_demande", "Prévision statistique de la demande d'un article sur un horizon en jours, "
              "avec intervalle de confiance.", {"sku": t, "horizon_jours": entier}, e.prevision_demande),
        Outil("comparer_fournisseurs", "Offres des fournisseurs pour un article : prix, délai, fiabilité, "
              "référencement, minimum de commande.", {"sku": t}, e.comparer_fournisseurs),
        Outil("lire_signaux", "Signaux récents non structurés : courriels fournisseurs, CRM, actualités.",
              {}, e.lire_signaux),
        Outil("creer_demande_achat", f"Crée une demande d'achat. Au-delà de {SEUIL_VALIDATION_FCFA} FCFA ou pour un "
              "fournisseur non référencé, elle part en validation chez l'acheteur.",
              {"sku": t, "fournisseur": t, "quantite": entier, "justification": t}, e.creer_demande_achat),
        Outil("alerter_acheteur", "Alerte l'acheteur sur un risque qui demande une décision humaine.",
              {"sku": t, "niveau": {"type": "string", "enum": ["info", "attention", "critique"]}, "message": t},
              e.alerter_acheteur),
    ]
