"""Cas 1 · Service client — outils de l'agent de résolution de tickets.

Les données sont chargées depuis `donnees/` (fichiers JSON fictifs) ; en
production, chaque fonction appellerait l'API du système concerné
(gestion des tickets, ERP, base de connaissances, système de paiement).
"""

from __future__ import annotations

import json
from pathlib import Path

from noyau import ErreurOutil, Outil
from noyau.recherche import rechercher

DOSSIER = Path(__file__).parent / "donnees"
SEUIL_REMBOURSEMENT_FCFA = 50_000


def _charger(nom: str):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


class Etat:
    """État du « système d'information » simulé, isolé pour chaque exécution."""

    def __init__(self):
        self.clients = {c["id"]: c for c in _charger("clients.json")}
        self.commandes = {c["numero"]: c for c in _charger("commandes.json")}
        self.articles = _charger("base_connaissances.json")
        self.tickets = {t["id"]: {**t, "statut": "ouvert"} for t in _charger("tickets.json")}
        self.remboursements: list[dict] = []
        self.reponses: list[dict] = []
        self.escalades: list[dict] = []

    # --------------------------------------------------------------- lecture
    def lire_ticket(self, ticket_id: str) -> dict:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            raise ErreurOutil(f"Ticket {ticket_id} introuvable.")
        return {"ticket": ticket, "client": self.clients[ticket["client_id"]]}

    def chercher_base_connaissances(self, requete: str) -> list[dict]:
        trouves = rechercher(self.articles, requete, ("titre", "mots_cles"))
        return [{"id": a["id"], "titre": a["titre"], "contenu": a["contenu"]} for a in trouves]

    def consulter_commande(self, numero: str) -> dict:
        commande = self.commandes.get(numero.upper().strip())
        if not commande:
            raise ErreurOutil(f"Commande {numero} introuvable. Vérifiez le numéro auprès du client.")
        return commande

    # --------------------------------------------------------------- actions
    def rembourser(self, ticket_id: str, numero: str, montant_fcfa: int, motif: str) -> dict:
        ticket = self.lire_ticket(ticket_id)["ticket"]
        commande = self.consulter_commande(numero)
        if commande["client_id"] != ticket["client_id"]:
            raise ErreurOutil("Cette commande n'appartient pas au client du ticket.")
        client = self.clients[ticket["client_id"]]
        deja = sum(r["montant_fcfa"] for r in self.remboursements if r["numero"] == commande["numero"])
        if montant_fcfa <= 0 or montant_fcfa + deja > commande["total"]:
            raise ErreurOutil("Montant invalide : il dépasse le total de la commande.")
        # Garde-fou codé en dur : l'agent ne PEUT PAS dépasser son mandat.
        if montant_fcfa > SEUIL_REMBOURSEMENT_FCFA or client["sensible"]:
            raise ErreurOutil(
                f"Remboursement hors mandat (seuil {SEUIL_REMBOURSEMENT_FCFA} FCFA, client sensible : "
                f"{client['sensible']}). Utilisez l'outil escalader."
            )
        operation = {"ticket_id": ticket_id, "numero": commande["numero"], "montant_fcfa": montant_fcfa,
                     "motif": motif, "reference": f"RMB-{len(self.remboursements) + 1:04d}"}
        self.remboursements.append(operation)
        return {"statut": "remboursement effectué", **operation}

    def repondre_client(self, ticket_id: str, message: str) -> dict:
        self.lire_ticket(ticket_id)
        self.reponses.append({"ticket_id": ticket_id, "message": message})
        self.tickets[ticket_id]["statut"] = "résolu"
        return {"statut": "réponse envoyée, ticket résolu", "ticket_id": ticket_id}

    def escalader(self, ticket_id: str, priorite: str, resume: str, proposition: str) -> dict:
        self.lire_ticket(ticket_id)
        self.escalades.append({"ticket_id": ticket_id, "priorite": priorite, "resume": resume,
                               "proposition": proposition})
        self.tickets[ticket_id]["statut"] = "escaladé"
        return {"statut": "transmis à un superviseur", "ticket_id": ticket_id, "priorite": priorite}

    def bilan(self) -> dict:
        return {"tickets": {k: v["statut"] for k, v in self.tickets.items()},
                "remboursements": self.remboursements, "reponses": self.reponses, "escalades": self.escalades}


def construire_outils(e: Etat) -> list[Outil]:
    texte = {"type": "string"}
    return [
        Outil("lire_ticket", "Lit un ticket de support et la fiche du client associé. "
              "À appeler en premier pour tout ticket.", {"ticket_id": texte}, e.lire_ticket),
        Outil("chercher_base_connaissances", "Recherche dans la base de connaissances (politiques, délais, "
              "règles de remboursement). Toujours vérifier la politique avant de répondre ou d'agir.",
              {"requete": {"type": "string", "description": "Mots clés en français"}}, e.chercher_base_connaissances),
        Outil("consulter_commande", "Renvoie le statut, les lignes, le total et le suivi d'une commande "
              "(numéro au format CMD-1234).", {"numero": texte}, e.consulter_commande),
        Outil("rembourser", f"Rembourse un montant en FCFA sur une commande. Autorisé seulement jusqu'à "
              f"{SEUIL_REMBOURSEMENT_FCFA} FCFA et pour un client non sensible ; sinon, escalader.",
              {"ticket_id": texte, "numero": texte, "montant_fcfa": {"type": "integer"}, "motif": texte}, e.rembourser),
        Outil("repondre_client", "Envoie la réponse finale au client et marque le ticket résolu. "
              "Ne pas utiliser si le ticket est escaladé.", {"ticket_id": texte, "message": texte}, e.repondre_client),
        Outil("escalader", "Transmet le ticket à un superviseur humain avec un résumé et une proposition. "
              "À utiliser pour tout cas hors mandat, ambigu, conflictuel ou suspect.",
              {"ticket_id": texte, "priorite": {"type": "string", "enum": ["normale", "haute", "urgente"]},
               "resume": texte, "proposition": texte}, e.escalader),
    ]
