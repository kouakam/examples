"""Cas 6 · Ventes — outils de l'agent de qualification et de préparation.

`rechercher_web` interroge un petit corpus local (`corpus_web.json`) pour que
l'exemple soit reproductible et hors ligne. En production, on le remplacerait
par l'outil serveur de recherche web de l'API (type `web_search_20260209`).

L'agent prépare, le commercial décide : aucun courriel n'est envoyé, et
aucun brouillon n'est rédigé sans consentement à la prospection.
"""

from __future__ import annotations

import json
from pathlib import Path

from noyau import ErreurOutil, Outil
from noyau.recherche import rechercher

DOSSIER = Path(__file__).parent / "donnees"
SORTIE = Path(__file__).resolve().parent.parent / "sortie" / "cas6"


def _charger(nom: str):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


class Etat:
    def __init__(self):
        self.prospects = {p["id"]: p for p in _charger("prospects.json")}
        self.corpus = _charger("corpus_web.json")
        self.crm = {c["entreprise"]: c for c in _charger("crm.json")}
        self.brouillons: list[dict] = []
        self.mises_a_jour: list[dict] = []

    def _prospect(self, prospect_id: str) -> dict:
        if prospect_id not in self.prospects:
            raise ErreurOutil(f"Prospect {prospect_id} introuvable.")
        return self.prospects[prospect_id]

    def lire_prospect(self, prospect_id: str) -> dict:
        return self._prospect(prospect_id)

    def lire_profil_client_ideal(self) -> str:
        return (DOSSIER / "profil_client_ideal.md").read_text(encoding="utf-8")

    def rechercher_web(self, requete: str) -> list[dict]:
        resultats = rechercher(self.corpus, requete, ("titre", "mots_cles"), n=3)
        return [{k: r[k] for k in ("titre", "source", "date", "texte")} for r in resultats] or \
            [{"resultat": "aucune information publique trouvée"}]

    def lire_crm(self, entreprise: str) -> dict:
        return self.crm.get(entreprise, {"entreprise": entreprise, "statut": "inconnu du CRM", "historique": []})

    def rediger_brouillon(self, prospect_id: str, objet: str, corps: str) -> dict:
        prospect = self._prospect(prospect_id)
        if not prospect["consentement_prospection"]:
            raise ErreurOutil("Pas de consentement à la prospection : aucun courriel ne peut être préparé.")
        SORTIE.mkdir(parents=True, exist_ok=True)
        fichier = SORTIE / f"brouillon_{prospect_id}.md"
        fichier.write_text(f"Objet : {objet}\n\n{corps}\n", encoding="utf-8")
        self.brouillons.append({"prospect_id": prospect_id, "objet": objet, "fichier": str(fichier.name)})
        return {"statut": "brouillon enregistré, en attente de validation du commercial",
                "fichier": f"sortie/cas6/{fichier.name}"}

    def mettre_a_jour_crm(self, prospect_id: str, score: int, note: str, prochaine_etape: str) -> dict:
        prospect = self._prospect(prospect_id)
        if not 0 <= score <= 100:
            raise ErreurOutil("Le score doit être compris entre 0 et 100.")
        maj = {"prospect_id": prospect_id, "entreprise": prospect["entreprise"], "score": score,
               "note": note, "prochaine_etape": prochaine_etape}
        self.mises_a_jour.append(maj)
        return {"statut": "CRM mis à jour", **maj}

    def bilan(self) -> dict:
        return {"crm": self.mises_a_jour, "brouillons": self.brouillons}


def construire_outils(e: Etat) -> list[Outil]:
    t = {"type": "string"}
    return [
        Outil("lire_prospect", "Fiche du prospect : entreprise, contact, source, message, consentement.",
              {"prospect_id": t}, e.lire_prospect),
        Outil("lire_profil_client_ideal", "Critères du profil client idéal de l'entreprise.", {},
              e.lire_profil_client_ideal),
        Outil("rechercher_web", "Recherche d'informations publiques sur une entreprise (activité, taille, actualités).",
              {"requete": t}, e.rechercher_web),
        Outil("lire_crm", "Historique de l'entreprise dans le CRM (nom exact de l'entreprise).",
              {"entreprise": t}, e.lire_crm),
        Outil("rediger_brouillon", "Enregistre un brouillon de premier courriel personnalisé (jamais envoyé "
              "automatiquement). Refusé sans consentement à la prospection.",
              {"prospect_id": t, "objet": t, "corps": t}, e.rediger_brouillon),
        Outil("mettre_a_jour_crm", "Enregistre le score d'adéquation (0 à 100), une note de préparation "
              "factuelle et la prochaine étape.",
              {"prospect_id": t, "score": {"type": "integer"}, "note": t, "prochaine_etape": t},
              e.mettre_a_jour_crm),
    ]
