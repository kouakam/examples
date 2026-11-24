"""Cas 2 · Finance — outils de l'agent comptes fournisseurs.

Le modèle lit la facture brute (texte libre, formats hétérogènes) et en
extrait les champs. Tout le reste est du code déterministe : rapprochement
à trois voies, contrôle du fournisseur, détection des doublons, calcul de
TVA. On ne demande pas à un LLM de faire de l'arithmétique comptable.
"""

from __future__ import annotations

import json
from pathlib import Path

from noyau import ErreurOutil, Outil

DOSSIER = Path(__file__).parent / "donnees"
SEUIL_ECART_PCT = 2.0
TAUX_TVA = 0.1925


def _charger(nom: str):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


def _normaliser_compte(compte: str) -> str:
    return "".join(compte.split()).upper()


class Etat:
    def __init__(self):
        self.fournisseurs = {f["id"]: f for f in _charger("fournisseurs.json")}
        self.bons = {b["numero"]: b for b in _charger("bons_commande.json")}
        self.receptions = {r["bon_commande"]: r for r in _charger("receptions.json")}
        self.contrats = {c["fournisseur_id"]: c for c in _charger("contrats.json")}
        self.paiements = _charger("paiements_historique.json")
        self.rapprochements: dict[str, dict] = {}
        self.approbations: dict[str, str] = {}
        self.lot_paiement: list[dict] = []
        self.bloquees: list[dict] = []

    # --------------------------------------------------------------- lecture
    def lister_factures_a_traiter(self) -> list[str]:
        return sorted(p.stem for p in (DOSSIER / "factures").glob("*.txt"))

    def lire_facture(self, numero_facture: str) -> str:
        chemin = DOSSIER / "factures" / f"{numero_facture.strip()}.txt"
        if not chemin.is_file():
            raise ErreurOutil(f"Facture {numero_facture} introuvable.")
        return chemin.read_text(encoding="utf-8")

    def consulter_fournisseur(self, nom: str) -> dict:
        cle = nom.lower().replace("sarl", "").strip()
        for f in self.fournisseurs.values():
            if cle in f["nom"].lower() or f["nom"].lower().replace(" sarl", "") in cle:
                return f
        raise ErreurOutil(f"Fournisseur « {nom} » absent du fichier maître : facture à bloquer.")

    def lire_bon_commande(self, numero: str) -> dict:
        if numero not in self.bons:
            raise ErreurOutil(f"Bon de commande {numero} introuvable.")
        return self.bons[numero]

    def lire_reception(self, numero_bc: str) -> dict:
        if numero_bc not in self.receptions:
            raise ErreurOutil(f"Aucune réception enregistrée pour {numero_bc} : marchandise non reçue.")
        return self.receptions[numero_bc]

    def chercher_contrat(self, fournisseur_id: str) -> dict:
        return self.contrats.get(fournisseur_id) or {"texte": "Aucun contrat enregistré."}

    def verifier_paiements_anterieurs(self, numero_facture: str) -> dict:
        deja = [p for p in self.paiements if p["facture"] == numero_facture]
        return {"deja_payee": bool(deja), "paiements": deja}

    # --------------------------------------------------------------- contrôles
    def rapprocher(self, numero_facture: str, numero_bc: str, lignes: list[dict]) -> dict:
        """Rapprochement à trois voies : facture / bon de commande / réception."""
        bc = self.lire_bon_commande(numero_bc)
        rec = self.lire_reception(numero_bc)
        resultat, conforme = [], True
        for ligne in lignes:
            cible = next((l for l in bc["lignes"] if l["article"].lower() in ligne["article"].lower()
                          or ligne["article"].lower() in l["article"].lower()), None)
            if cible is None:
                resultat.append({"article": ligne["article"], "probleme": "article absent du bon de commande"})
                conforme = False
                continue
            recu = next(l["quantite_recue"] for l in rec["lignes"] if l["article"] == cible["article"])
            ecart = round((ligne["prix_unitaire"] - cible["prix_unitaire"]) / cible["prix_unitaire"] * 100, 2)
            ok = abs(ecart) <= SEUIL_ECART_PCT and ligne["quantite"] <= recu
            conforme &= ok
            resultat.append({"article": cible["article"], "prix_bc": cible["prix_unitaire"],
                             "prix_facture": ligne["prix_unitaire"], "ecart_prix_pct": ecart,
                             "quantite_commandee": cible["quantite"], "quantite_recue": recu,
                             "quantite_facturee": ligne["quantite"], "conforme": ok})
        synthese = {"numero_facture": numero_facture, "bon_commande": numero_bc, "conforme": conforme,
                    "seuil_ecart_pct": SEUIL_ECART_PCT, "lignes": resultat}
        self.rapprochements[numero_facture] = synthese
        return synthese

    # --------------------------------------------------------------- actions
    def demander_approbation_ecart(self, numero_facture: str, ecart_pct: float, justification: str) -> dict:
        # Cet outil est déclaré « sensible » : il n'est exécuté qu'après accord humain.
        self.approbations[numero_facture] = justification
        return {"statut": "écart approuvé par le contrôleur de gestion", "numero_facture": numero_facture}

    def preparer_ecriture(self, numero_facture: str, fournisseur_id: str, montant_ht: int,
                          montant_tva: int, montant_ttc: int, compte_bancaire: str) -> dict:
        rap = self.rapprochements.get(numero_facture)
        if rap is None:
            raise ErreurOutil("Rapprochement non effectué : appelez d'abord rapprocher.")
        if not rap["conforme"] and numero_facture not in self.approbations:
            raise ErreurOutil("Écart hors tolérance non approuvé : utilisez demander_approbation_ecart.")
        if self.verifier_paiements_anterieurs(numero_facture)["deja_payee"]:
            raise ErreurOutil("Facture déjà payée : doublon, à bloquer.")
        fournisseur = self.fournisseurs.get(fournisseur_id)
        if fournisseur is None:
            raise ErreurOutil("Fournisseur inconnu.")
        if _normaliser_compte(compte_bancaire) != _normaliser_compte(fournisseur["compte_bancaire"]):
            raise ErreurOutil("Compte bancaire différent du fichier maître : risque de fraude, bloquer la facture.")
        if abs(round(montant_ht * TAUX_TVA) - montant_tva) > 1 or montant_ht + montant_tva != montant_ttc:
            raise ErreurOutil(f"Montants incohérents : TVA attendue {round(montant_ht * TAUX_TVA)} FCFA.")
        ecriture = {"numero_facture": numero_facture, "fournisseur": fournisseur["nom"],
                    "debit_601_achats": montant_ht, "debit_4452_tva": montant_tva,
                    "credit_401_fournisseur": montant_ttc, "compte_bancaire": fournisseur["compte_bancaire"],
                    "statut": "dans le lot de paiement, à valider par le trésorier"}
        self.lot_paiement.append(ecriture)
        return ecriture

    def bloquer_facture(self, numero_facture: str, motif: str, alerte_fraude: bool) -> dict:
        self.bloquees.append({"numero_facture": numero_facture, "motif": motif, "alerte_fraude": alerte_fraude})
        return {"statut": "facture bloquée", "alerte_envoyee_a": "contrôle interne" if alerte_fraude else "comptable"}

    def bilan(self) -> dict:
        return {"lot_paiement": self.lot_paiement, "factures_bloquees": self.bloquees,
                "ecarts_approuves": self.approbations}


def construire_outils(e: Etat) -> list[Outil]:
    t = {"type": "string"}
    ligne = {"type": "object", "additionalProperties": False, "required": ["article", "quantite", "prix_unitaire"],
             "properties": {"article": t, "quantite": {"type": "integer"}, "prix_unitaire": {"type": "integer"}}}
    entier = {"type": "integer"}
    return [
        Outil("lire_facture", "Renvoie le texte brut d'une facture fournisseur (format libre, à analyser).",
              {"numero_facture": t}, e.lire_facture),
        Outil("consulter_fournisseur", "Fiche du fichier maître fournisseurs (id, compte bancaire officiel) "
              "à partir du nom figurant sur la facture.", {"nom": t}, e.consulter_fournisseur),
        Outil("verifier_paiements_anterieurs", "Indique si une facture a déjà été payée (détection des doublons).",
              {"numero_facture": t}, e.verifier_paiements_anterieurs),
        Outil("chercher_contrat", "Texte du contrat et des avenants d'un fournisseur (prix convenus, conditions).",
              {"fournisseur_id": t}, e.chercher_contrat),
        Outil("lire_bon_commande", "Bon de commande (lignes, quantités, prix convenus).", {"numero": t},
              e.lire_bon_commande),
        Outil("rapprocher", f"Rapprochement à trois voies facture / bon de commande / réception. Passez les lignes "
              f"extraites de la facture. Tolérance de prix : {SEUIL_ECART_PCT} %.",
              {"numero_facture": t, "numero_bc": t, "lignes": {"type": "array", "items": ligne}}, e.rapprocher),
        Outil("demander_approbation_ecart", "Soumet un écart de prix hors tolérance au contrôleur de gestion, avec "
              "une justification citant le contrat ou l'avenant. Exécuté seulement si un humain approuve.",
              {"numero_facture": t, "ecart_pct": {"type": "number"}, "justification": t},
              e.demander_approbation_ecart, sensible=True),
        Outil("preparer_ecriture", "Prépare l'écriture comptable et ajoute la facture au lot de paiement (le "
              "paiement final reste validé par le trésorier). Utiliser le compte bancaire LU SUR LA FACTURE.",
              {"numero_facture": t, "fournisseur_id": t, "montant_ht": entier, "montant_tva": entier,
               "montant_ttc": entier, "compte_bancaire": t}, e.preparer_ecriture),
        Outil("bloquer_facture", "Bloque une facture (doublon, fraude suspectée, anomalie non résolue) et alerte "
              "le contrôle interne si alerte_fraude est vrai.",
              {"numero_facture": t, "motif": t, "alerte_fraude": {"type": "boolean"}}, e.bloquer_facture),
    ]
