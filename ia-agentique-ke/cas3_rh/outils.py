"""Cas 3 · Ressources humaines — outils de l'agent d'intégration.

L'agent coordonne un processus transversal (RH, TI, services généraux,
formation) et répond aux questions courantes. Il ne prend AUCUNE décision
sur la rémunération, l'évaluation ou le contrat : ces sujets sont transmis
au service RH. Les accès sensibles exigent l'accord du gestionnaire.
"""

from __future__ import annotations

import json
from pathlib import Path

from noyau import ErreurOutil, Outil
from noyau.recherche import rechercher

DOSSIER = Path(__file__).parent / "donnees"


def _charger(nom: str):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


class Etat:
    def __init__(self):
        self.embauches = {e["id"]: e for e in _charger("embauches.json")}
        self.modeles = _charger("modeles_integration.json")
        self.sessions = _charger("formations.json")
        self.politiques = _charger("politiques_rh.json")
        self.questions = {q["id"]: q for q in _charger("questions.json")}
        self.demandes_ti: list[dict] = []
        self.commandes_materiel: list[dict] = []
        self.inscriptions: list[dict] = []
        self.notifications: list[dict] = []
        self.transmissions_rh: list[dict] = []

    def _employe(self, employe_id: str) -> dict:
        if employe_id not in self.embauches:
            raise ErreurOutil(f"Employé {employe_id} introuvable dans le SIRH.")
        return self.embauches[employe_id]

    def _acces(self, employe_id: str, systeme: str) -> dict:
        poste = self._employe(employe_id)["poste"]
        for acces in self.modeles[poste]["acces"]:
            if acces["systeme"].lower() == systeme.lower():
                return acces
        raise ErreurOutil(f"« {systeme} » ne fait pas partie du modèle d'accès du poste {poste}.")

    # --------------------------------------------------------------- lecture
    def lire_dossier_embauche(self, employe_id: str) -> dict:
        return self._employe(employe_id)

    def obtenir_modele_integration(self, poste: str) -> dict:
        if poste not in self.modeles:
            raise ErreurOutil(f"Aucun modèle pour le poste {poste}. Postes : {', '.join(self.modeles)}.")
        return self.modeles[poste]

    def lire_question(self, question_id: str) -> dict:
        if question_id not in self.questions:
            raise ErreurOutil(f"Question {question_id} introuvable.")
        q = self.questions[question_id]
        return {**q, "employe": self._employe(q["employe_id"])}

    def chercher_politiques_rh(self, requete: str) -> list[dict]:
        return [{"id": p["id"], "titre": p["titre"], "texte": p["texte"]}
                for p in rechercher(self.politiques, requete, ("titre", "mots_cles"))]

    # --------------------------------------------------------------- actions
    def demander_acces_ti(self, employe_id: str, systeme: str, justification: str) -> dict:
        acces = self._acces(employe_id, systeme)
        if acces["sensible"]:
            raise ErreurOutil("Accès sensible : utilisez demander_acces_sensible (accord du gestionnaire requis).")
        return self._enregistrer_acces(employe_id, acces, justification, "créé")

    def demander_acces_sensible(self, employe_id: str, systeme: str, justification: str) -> dict:
        acces = self._acces(employe_id, systeme)  # outil « sensible » : exécuté après accord humain
        return self._enregistrer_acces(employe_id, acces, justification, "créé après accord du gestionnaire")

    def _enregistrer_acces(self, employe_id, acces, justification, statut) -> dict:
        demande = {"employe_id": employe_id, "systeme": acces["systeme"], "niveau": acces["niveau"],
                   "justification": justification, "statut": statut,
                   "ticket_ti": f"TI-{4100 + len(self.demandes_ti)}"}
        self.demandes_ti.append(demande)
        return demande

    def commander_materiel(self, employe_id: str, articles: list[str]) -> dict:
        employe = self._employe(employe_id)
        commande = {"employe_id": employe_id, "articles": articles, "livraison_site": employe["site"],
                    "avant_le": employe["date_arrivee"], "reference": f"MAT-{300 + len(self.commandes_materiel)}"}
        self.commandes_materiel.append(commande)
        return commande

    def planifier_formation(self, employe_id: str, formation: str) -> dict:
        employe = self._employe(employe_id)
        possibles = [s for s in self.sessions if s["formation"].lower() == formation.lower()
                     and s["site"] in (employe["site"], "en ligne") and s["date"] >= employe["date_arrivee"]]
        if not possibles:
            raise ErreurOutil(f"Aucune session de « {formation} » après l'arrivée sur le site {employe['site']} : "
                              "signaler au service formation.")
        session = min(possibles, key=lambda s: s["date"])
        inscription = {"employe_id": employe_id, **session}
        self.inscriptions.append(inscription)
        return inscription

    def notifier(self, destinataire: str, objet: str, message: str) -> dict:
        self.notifications.append({"destinataire": destinataire, "objet": objet, "message": message})
        return {"statut": "envoyé", "destinataire": destinataire}

    def transmettre_rh(self, employe_id: str, sujet: str, motif: str) -> dict:
        self._employe(employe_id)
        self.transmissions_rh.append({"employe_id": employe_id, "sujet": sujet, "motif": motif})
        return {"statut": "transmis au service RH", "delai_reponse": "2 jours ouvrables"}

    def bilan(self) -> dict:
        return {"demandes_ti": self.demandes_ti, "materiel": self.commandes_materiel,
                "formations": self.inscriptions, "notifications": self.notifications,
                "transmis_rh": self.transmissions_rh}


def construire_outils(e: Etat) -> list[Outil]:
    t = {"type": "string"}
    return [
        Outil("lire_dossier_embauche", "Dossier SIRH d'un nouvel employé (poste, site, date d'arrivée, gestionnaire).",
              {"employe_id": t}, e.lire_dossier_embauche),
        Outil("obtenir_modele_integration", "Modèle d'intégration d'un poste : accès, matériel, formations.",
              {"poste": t}, e.obtenir_modele_integration),
        Outil("lire_question", "Question posée par un employé, avec son dossier.", {"question_id": t}, e.lire_question),
        Outil("chercher_politiques_rh", "Recherche dans les politiques RH internes. Toujours citer la politique.",
              {"requete": t}, e.chercher_politiques_rh),
        Outil("demander_acces_ti", "Crée une demande d'accès standard (non sensible) prévue par le modèle du poste.",
              {"employe_id": t, "systeme": t, "justification": t}, e.demander_acces_ti),
        Outil("demander_acces_sensible", "Crée une demande d'accès sensible (finances, zones techniques). "
              "Soumise à l'accord du gestionnaire avant exécution.",
              {"employe_id": t, "systeme": t, "justification": t}, e.demander_acces_sensible, sensible=True),
        Outil("commander_materiel", "Commande le matériel prévu, livré sur le site avant la date d'arrivée.",
              {"employe_id": t, "articles": {"type": "array", "items": t}}, e.commander_materiel),
        Outil("planifier_formation", "Inscrit l'employé à la prochaine session d'une formation après son arrivée.",
              {"employe_id": t, "formation": t}, e.planifier_formation),
        Outil("notifier", "Envoie un message (gestionnaire, employé, service).",
              {"destinataire": t, "objet": t, "message": t}, e.notifier),
        Outil("transmettre_rh", "Transmet au service RH une question hors du périmètre de l'agent "
              "(rémunération, contrat, évaluation, conflit).", {"employe_id": t, "sujet": t, "motif": t},
              e.transmettre_rh),
    ]
