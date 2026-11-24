"""Client simulé : exécuter les cas pratiques sans clé d'API.

Le client simulé imite `client.beta.messages.create` du SDK Anthropic. À la
place du modèle, une *politique* Python déterministe décide de l'appel
d'outil suivant à partir de l'historique. Les outils, les données, la boucle,
les approbations et les traces sont exactement les mêmes qu'en mode réel.

À utiliser pour : tester l'installation, montrer le déroulement en classe
sans réseau, et servir de référence « workflow codé à la main » à comparer
avec le vrai agent (voir la diapositive « Workflow ou agent »).
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable


@dataclass
class Appel:
    nom: str
    entree: dict
    pensee: str = ""


@dataclass
class Parallele:
    appels: list[Appel]
    pensee: str = ""


@dataclass
class Fin:
    texte: str


@dataclass
class Historique:
    entrees: list[dict] = field(default_factory=list)  # {nom, entree, resultat, erreur}

    def appels(self, nom: str) -> list[dict]:
        return [e for e in self.entrees if e["nom"] == nom]

    def a_appele(self, nom: str) -> bool:
        return bool(self.appels(nom))

    def resultat(self, nom: str) -> Any:
        appels = self.appels(nom)
        return appels[-1]["resultat"] if appels else None


Politique = Callable[[str, Historique], "Appel | Parallele | Fin"]


def _attr(objet, cle, defaut=None):
    return objet.get(cle, defaut) if isinstance(objet, dict) else getattr(objet, cle, defaut)


def _historique(messages: list[dict]) -> Historique:
    en_attente: dict[str, tuple[str, dict]] = {}
    h = Historique()
    for message in messages:
        contenu = message["content"]
        if isinstance(contenu, str):
            continue
        for bloc in contenu:
            type_ = _attr(bloc, "type")
            if type_ == "tool_use":
                en_attente[_attr(bloc, "id")] = (_attr(bloc, "name"), dict(_attr(bloc, "input") or {}))
            elif type_ == "tool_result":
                nom, entree = en_attente.pop(_attr(bloc, "tool_use_id"), ("?", {}))
                brut = _attr(bloc, "content")
                try:
                    resultat = json.loads(brut)
                except (TypeError, ValueError):
                    resultat = brut
                h.entrees.append({"nom": nom, "entree": entree, "resultat": resultat,
                                  "erreur": bool(_attr(bloc, "is_error", False))})
    return h


class ClientSimule:
    def __init__(self, politique: Politique):
        self.politique = politique
        self._compteur = itertools.count(1)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._creer))

    def _bloc_outil(self, appel: Appel):
        return SimpleNamespace(type="tool_use", id=f"toolu_sim_{next(self._compteur)}",
                               name=appel.nom, input=appel.entree)

    def _creer(self, *, messages: list[dict], **_ignores):
        demande = messages[0]["content"]
        decision = self.politique(demande, _historique(messages))
        usage = SimpleNamespace(input_tokens=0, output_tokens=0)
        if isinstance(decision, Fin):
            contenu = [SimpleNamespace(type="text", text=decision.texte)]
            return SimpleNamespace(content=contenu, stop_reason="end_turn", usage=usage, model="simulation")
        appels = decision.appels if isinstance(decision, Parallele) else [decision]
        pensee = decision.pensee
        contenu = ([SimpleNamespace(type="text", text=pensee)] if pensee else []) + [
            self._bloc_outil(a) for a in appels
        ]
        return SimpleNamespace(content=contenu, stop_reason="tool_use", usage=usage, model="simulation")
