"""Cas 5 · Chaîne d'approvisionnement — agent de réapprovisionnement.

Exécution :
    python -m cas5_approvisionnement.agent                 # avec l'API Anthropic
    python -m cas5_approvisionnement.agent --simulation    # sans clé d'API
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from noyau import Agent, Appel, Fin, Historique, Parallele
from noyau.cli import afficher_json, lancer

from .outils import SEMAINES_COUVERTURE_CIBLE, Etat, construire_outils

SYSTEME = f"""Tu es l'agent de réapprovisionnement de Distribution Boréal. Chaque nuit :
1. Analyse les stocks et lis les signaux récents (fournisseurs, CRM, actualités).
2. Pour chaque article dont le stock projeté à la fin du délai fournisseur passerait sous le
   stock de sécurité, utilise la prévision statistique et compare les fournisseurs.
3. Choisis l'offre en arbitrant prix, délai et fiabilité ; tiens compte des signaux (un retard
   annoncé allonge le délai réel ; une commande client annoncée s'ajoute à la prévision).
4. Crée une demande d'achat couvrant le délai + {SEMAINES_COUVERTURE_CIBLE} semaines, avec une justification
   chiffrée (demande prévue, stock, délai, choix du fournisseur).
5. Alerte l'acheteur pour tout risque que tu ne peux pas traiter seul.
Ne commande pas un article qui n'en a pas besoin. Termine par une synthèse en quelques lignes."""

ETAT = Etat()


def construire(client=None, approbateur=None, journal=None, max_etapes=25) -> Agent:
    return Agent("cas5-approvisionnement", SYSTEME, construire_outils(ETAT), client=client,
                 approbateur=approbateur, journal=journal, max_etapes=max(max_etapes, 25))


CAS = [("NUIT", "Lance l'analyse de réapprovisionnement de cette nuit pour tous les articles.")]


# --------------------------------------------------------------- simulation
def _retard_annonce(fournisseur: str, signaux: list[dict]) -> int:
    return 14 if any(s["auteur"] == fournisseur and "retard" in s["texte"].lower() for s in signaux) else 0


def _commande_annoncee(sku: str, signaux: list[dict]) -> int:
    for s in signaux:
        if sku in s["texte"] and "commander" in s["texte"]:
            return int(next(m for m in s["texte"].split() if m.isdigit()))
    return 0


def politique_simulee(demande: str, h: Historique):
    if not h.a_appele("analyser_stocks"):
        return Parallele([Appel("analyser_stocks", {}), Appel("lire_signaux", {})],
                         "Je commence par l'état des stocks et les signaux de la semaine.")
    stocks, signaux = h.resultat("analyser_stocks"), h.resultat("lire_signaux")
    deja = {x["entree"]["sku"] for x in h.appels("comparer_fournisseurs")}
    for s in stocks:
        if s["sku"] not in deja:
            return Appel("comparer_fournisseurs", {"sku": s["sku"]})
    traites = {x["entree"]["sku"] for x in h.appels("creer_demande_achat") + h.appels("alerter_acheteur")}
    offres = {x["entree"]["sku"]: x["resultat"] for x in h.appels("comparer_fournisseurs")}
    for s in stocks:
        if s["sku"] in traites:
            continue
        # Délai réel = délai annoncé + retard signalé ; on retient la meilleure offre référencée fiable.
        candidates = sorted((o for o in offres[s["sku"]] if o["reference"]),
                            key=lambda o: (o["delai_jours"] + _retard_annonce(o["fournisseur"], signaux),
                                           -o["fiabilite"], o["prix_unitaire"]))
        o = candidates[0]
        delai = o["delai_jours"] + _retard_annonce(o["fournisseur"], signaux)
        hebdo = s["demande_hebdo_prevue"]
        extra = _commande_annoncee(s["sku"], signaux)
        stock_fin_delai = s["stock"] + s["en_commande"] - hebdo * delai / 7 - extra
        if stock_fin_delai >= s["stock_securite"]:
            continue
        besoin = math.ceil(hebdo * (delai / 7 + SEMAINES_COUVERTURE_CIBLE) + s["stock_securite"] + extra
                           - s["stock"] - s["en_commande"])
        quantite = max(besoin, o["minimum"])
        return Appel("creer_demande_achat", {
            "sku": s["sku"], "fournisseur": o["fournisseur"], "quantite": quantite,
            "justification": f"Demande prévue {hebdo}/semaine" + (f" + commande client annoncée de {extra}" if extra else "")
                             + f" ; stock {s['stock']} (+{s['en_commande']} en commande) ; délai {delai} j ; "
                             f"stock projeté {round(stock_fin_delai)} < sécurité {s['stock_securite']}."})
    lignes = [f"{d['resultat']['sku']} : {d['resultat']['quantite']} chez {d['resultat']['fournisseur']} "
              f"({d['resultat']['statut']})" for d in h.appels("creer_demande_achat") if not d["erreur"]]
    return Fin("Analyse terminée. Demandes d'achat : " + ("; ".join(lignes) or "aucune") + ".")


def bilan() -> None:
    afficher_json("Demandes d'achat et alertes", ETAT.bilan())
    sortie = Path(__file__).resolve().parent.parent / "sortie" / "cas5_bilan.json"
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(json.dumps(ETAT.bilan(), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    lancer("cas5", "Cas 5 · Agent de réapprovisionnement", construire, CAS, politique_simulee, bilan)
