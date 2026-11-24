"""Interface en ligne de commande commune à tous les cas pratiques."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Callable

from .agent import Agent, Resultat, approbation_automatique, approbation_console
from .journal import Journal
from .simulation import ClientSimule, Politique

# construire(client, approbateur, journal, max_etapes) -> Agent
Constructeur = Callable[..., Agent]


def lancer(nom: str, titre: str, construire: Constructeur, cas: list[tuple[str, str]],
           politique: Politique, apres: Callable[[], None] | None = None,
           argv: list[str] | None = None) -> list[tuple[str, Resultat]]:
    p = argparse.ArgumentParser(description=titre)
    p.add_argument("--simulation", action="store_true",
                   help="exécuter sans clé d'API, avec une politique déterministe à la place du modèle")
    p.add_argument("--id", help="n'exécuter qu'un seul cas du jeu d'exemples")
    groupe = p.add_mutually_exclusive_group()
    groupe.add_argument("--auto-approuver", action="store_true", help="approuver automatiquement les actions sensibles")
    groupe.add_argument("--auto-refuser", action="store_true", help="refuser automatiquement les actions sensibles")
    p.add_argument("--max-etapes", type=int, default=15)
    p.add_argument("--silencieux", action="store_true")
    a = p.parse_args(argv)

    if a.auto_approuver:
        approbateur = approbation_automatique(True)
    elif a.auto_refuser or not sys.stdin.isatty():
        approbateur = approbation_automatique(False)
    else:
        approbateur = approbation_console

    client = ClientSimule(politique) if a.simulation else None
    selection = [c for c in cas if a.id is None or c[0] == a.id]
    if not selection:
        p.error(f"identifiant inconnu : {a.id}. Choix : {', '.join(c[0] for c in cas)}")

    print(f"=== {titre} — mode {'SIMULATION (sans modèle)' if a.simulation else 'RÉEL (API Anthropic)'} ===")
    resultats = []
    for identifiant, demande in selection:
        journal = Journal(f"{nom}-{identifiant}", silencieux=a.silencieux)
        try:
            agent = construire(client=client, approbateur=approbateur, journal=journal, max_etapes=a.max_etapes)
            resultats.append((identifiant, agent.executer(demande)))
        except Exception as e:
            if type(e).__name__ in {"AuthenticationError", "PermissionDeniedError"}:
                sys.exit("Authentification impossible : définissez ANTHROPIC_API_KEY ou lancez avec --simulation.")
            raise

    print("\n=== SYNTHÈSE ===")
    for identifiant, r in resultats:
        outils = ", ".join(x["outil"] for x in r.appels_outils) or "aucun"
        print(f"- {identifiant:<10} {r.statut:<8} {r.etapes:>2} tours · "
              f"jetons {r.jetons_entree}/{r.jetons_sortie} · {r.duree_s:.1f}s · outils : {outils}")
    if apres:
        apres()
    return resultats


def afficher_json(titre: str, donnees) -> None:
    print(f"\n--- {titre} ---")
    print(json.dumps(donnees, ensure_ascii=False, indent=2, default=str))
