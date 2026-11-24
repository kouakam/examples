"""Boucle agentique commune aux sept cas pratiques.

Logiciel KE inc. · Séminaire « L'IA agentique en entreprise ».

L'agent suit le patron ReAct : à chaque tour, le modèle reçoit tout
l'historique et décide soit d'appeler un ou plusieurs outils, soit de
répondre. Le code ci-dessous ajoute ce qu'il faut pour un usage sérieux :
budget d'étapes, approbation humaine des outils sensibles, gestion des
erreurs d'outils, des refus et des réponses tronquées, et journalisation.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .journal import Journal

MODELE_PAR_DEFAUT = os.environ.get("KE_MODELE", "claude-opus-5-5")

# Repli automatique côté serveur si le modèle décline une requête
# (paramètre `fallbacks`). Mettre KE_SANS_REPLI=1 pour le désactiver,
# par exemple sur une plateforme qui ne le prend pas en charge.
REPLI_ACTIVE = os.environ.get("KE_SANS_REPLI", "") != "1"


class ErreurOutil(Exception):
    """Erreur métier renvoyée au modèle (is_error=True) pour qu'il s'adapte."""


@dataclass
class Outil:
    """Un outil exposé à l'agent.

    `parametres` contient les propriétés JSON Schema. Tous les paramètres
    sont obligatoires par défaut ; le mode strict garantit que le modèle
    produit des arguments conformes au schéma.
    """

    nom: str
    description: str
    parametres: dict
    fonction: Callable[..., Any]
    requis: list[str] | None = None
    sensible: bool = False  # exige une approbation humaine avant exécution

    def schema(self) -> dict:
        requis = list(self.parametres) if self.requis is None else self.requis
        return {
            "name": self.nom,
            "description": self.description,
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": self.parametres,
                "required": requis,
                "additionalProperties": False,
            },
        }


# Un approbateur reçoit (nom_outil, arguments) et renvoie (approuvé, motif).
Approbateur = Callable[[str, dict], "tuple[bool, str]"]


def approbation_console(nom: str, arguments: dict) -> tuple[bool, str]:
    """Demande la décision à la personne devant le terminal."""
    print("\n┌─ DEMANDE D'APPROBATION ─────────────────────────────")
    print(f"│ Outil : {nom}")
    for cle, valeur in arguments.items():
        print(f"│ {cle} : {valeur}")
    print("└─────────────────────────────────────────────────────")
    reponse = input("Approuver ? [o/N] ").strip().lower()
    if reponse in {"o", "oui", "y", "yes"}:
        return True, "approuvé par l'opérateur"
    motif = input("Motif du refus (facultatif) : ").strip()
    return False, motif or "refusé par l'opérateur"


def approbation_automatique(decision: bool) -> Approbateur:
    """Approbateur non interactif (tests, démonstrations en lot)."""

    def approuver(nom: str, arguments: dict) -> tuple[bool, str]:
        return decision, "approbation automatique" if decision else "refus automatique (mode lot)"

    return approuver


@dataclass
class Resultat:
    statut: str  # termine | limite | refus | tronque
    texte: str
    etapes: int
    appels_outils: list[dict] = field(default_factory=list)
    jetons_entree: int = 0
    jetons_sortie: int = 0
    duree_s: float = 0.0


def _texte(contenu) -> str:
    return "\n".join(b.text for b in contenu if getattr(b, "type", None) == "text").strip()


class Agent:
    def __init__(
        self,
        nom: str,
        systeme: str,
        outils: list[Outil],
        client=None,
        modele: str = MODELE_PAR_DEFAUT,
        max_etapes: int = 15,
        approbateur: Approbateur | None = None,
        journal: Journal | None = None,
        max_tokens: int = 16000,
    ):
        self.nom = nom
        self.systeme = systeme
        self.outils = {o.nom: o for o in outils}
        self.modele = modele
        self.max_etapes = max_etapes
        self.approbateur = approbateur or approbation_automatique(False)
        self.journal = journal or Journal(nom)
        self.max_tokens = max_tokens
        if client is None:
            import anthropic  # import tardif : le mode simulation n'en a pas besoin

            client = anthropic.Anthropic()
        self.client = client

    # ------------------------------------------------------------------ modèle
    def _appeler_modele(self, messages: list[dict]):
        parametres = dict(
            model=self.modele,
            max_tokens=self.max_tokens,
            system=self.systeme,
            tools=[o.schema() for o in self.outils.values()],
            messages=messages,
            cache_control={"type": "ephemeral"},  # met en cache système + outils + historique
        )
        if REPLI_ACTIVE:
            parametres["betas"] = ["server-side-fallback-2026-07-01"]
            parametres["fallbacks"] = "default"
        return self.client.beta.messages.create(**parametres)

    # ------------------------------------------------------------------ outils
    def _executer_outil(self, bloc) -> dict:
        nom, arguments = bloc.name, dict(bloc.input or {})
        self.journal.appel_outil(nom, arguments)
        outil = self.outils.get(nom)
        if outil is None:
            return self._resultat(bloc.id, f"Outil inconnu : {nom}", erreur=True)

        if outil.sensible:
            approuve, motif = self.approbateur(nom, arguments)
            self.journal.decision_humaine(nom, approuve, motif)
            if not approuve:
                return self._resultat(
                    bloc.id,
                    json.dumps({"statut": "refusé par un humain", "motif": motif}, ensure_ascii=False),
                )

        try:
            sortie = outil.fonction(**arguments)
            contenu = sortie if isinstance(sortie, str) else json.dumps(sortie, ensure_ascii=False, default=str)
            self.journal.resultat_outil(nom, contenu)
            return self._resultat(bloc.id, contenu)
        except ErreurOutil as e:
            self.journal.resultat_outil(nom, f"ERREUR : {e}", erreur=True)
            return self._resultat(bloc.id, str(e), erreur=True)
        except Exception as e:  # une panne d'outil ne doit pas faire tomber l'agent
            self.journal.resultat_outil(nom, f"ERREUR INTERNE : {e!r}", erreur=True)
            return self._resultat(bloc.id, f"Erreur interne de l'outil {nom} : {e}", erreur=True)

    @staticmethod
    def _resultat(identifiant: str, contenu: str, erreur: bool = False) -> dict:
        bloc = {"type": "tool_result", "tool_use_id": identifiant, "content": contenu}
        if erreur:
            bloc["is_error"] = True
        return bloc

    # ------------------------------------------------------------------ boucle
    def executer(self, demande: str) -> Resultat:
        debut = time.monotonic()
        self.journal.demande(demande)
        messages: list[dict] = [{"role": "user", "content": demande}]
        appels: list[dict] = []
        entree = sortie = 0

        for etape in range(1, self.max_etapes + 1):
            reponse = self._appeler_modele(messages)
            usage = getattr(reponse, "usage", None)
            entree += getattr(usage, "input_tokens", 0) or 0
            sortie += getattr(usage, "output_tokens", 0) or 0

            # On renvoie TOUT le contenu (blocs tool_use, réflexion, repli…).
            messages.append({"role": "assistant", "content": reponse.content})
            texte = _texte(reponse.content)
            if texte and reponse.stop_reason == "tool_use":
                self.journal.pensee(texte)

            def fin(statut: str, message: str) -> Resultat:
                r = Resultat(statut, message, etape, appels, entree, sortie, time.monotonic() - debut)
                self.journal.fin(r)
                return r

            if reponse.stop_reason == "pause_turn":
                continue
            if reponse.stop_reason == "refusal":
                return fin("refus", "Le modèle a décliné la demande : traitement manuel requis.")
            if reponse.stop_reason == "max_tokens":
                return fin("tronque", texte or "Réponse tronquée (max_tokens atteint).")
            if reponse.stop_reason != "tool_use":
                return fin("termine", texte)

            resultats = []
            for bloc in reponse.content:
                if getattr(bloc, "type", None) == "tool_use":
                    resultat = self._executer_outil(bloc)
                    resultats.append(resultat)
                    appels.append({"outil": bloc.name, "arguments": dict(bloc.input or {}),
                                   "erreur": resultat.get("is_error", False)})
            # Tous les résultats dans UN seul message : préserve les appels parallèles.
            messages.append({"role": "user", "content": resultats})

        r = Resultat("limite", "Budget d'étapes épuisé : escalade vers un humain.",
                     self.max_etapes, appels, entree, sortie, time.monotonic() - debut)
        self.journal.fin(r)
        return r
