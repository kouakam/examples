"""Journal lisible en console + trace JSONL pour l'observabilité."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
COULEUR = sys.stdout.isatty()


def _c(code: str, texte: str) -> str:
    return f"\033[{code}m{texte}\033[0m" if COULEUR else texte


def _court(texte: str, limite: int = 400) -> str:
    texte = " ".join(str(texte).split())
    return texte if len(texte) <= limite else texte[: limite - 1] + "…"


class Journal:
    def __init__(self, nom: str, silencieux: bool = False, dossier: Path | None = None):
        self.nom = nom
        self.silencieux = silencieux
        self.evenements: list[dict] = []
        dossier = dossier or RACINE / "traces"
        dossier.mkdir(parents=True, exist_ok=True)
        self.fichier = dossier / f"{nom}-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"

    def _ecrire(self, type_: str, **donnees) -> None:
        evt = {"t": round(time.time(), 3), "type": type_, **donnees}
        self.evenements.append(evt)
        with self.fichier.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False, default=str) + "\n")

    def _afficher(self, texte: str) -> None:
        if not self.silencieux:
            print(texte)

    def demande(self, texte: str) -> None:
        self._ecrire("demande", texte=texte)
        self._afficher("\n" + _c("1;37", "▶ DEMANDE  ") + _court(texte, 600))

    def pensee(self, texte: str) -> None:
        self._ecrire("pensee", texte=texte)
        self._afficher(_c("2", "  · " + _court(texte, 300)))

    def appel_outil(self, nom: str, arguments: dict) -> None:
        self._ecrire("appel_outil", outil=nom, arguments=arguments)
        self._afficher(_c("34", "  → tool_use    ") + f"{nom} {json.dumps(arguments, ensure_ascii=False)}")

    def resultat_outil(self, nom: str, contenu: str, erreur: bool = False) -> None:
        self._ecrire("resultat_outil", outil=nom, contenu=contenu, erreur=erreur)
        couleur = "31" if erreur else "33"
        self._afficher(_c(couleur, "  ← tool_result ") + _court(contenu, 300))

    def decision_humaine(self, nom: str, approuve: bool, motif: str) -> None:
        self._ecrire("decision_humaine", outil=nom, approuve=approuve, motif=motif)
        etiquette = "APPROUVÉ" if approuve else "REFUSÉ"
        self._afficher(_c("35", f"  ✋ humain      {etiquette} ({motif})"))

    def fin(self, resultat) -> None:
        self._ecrire("fin", statut=resultat.statut, texte=resultat.texte, etapes=resultat.etapes,
                     jetons_entree=resultat.jetons_entree, jetons_sortie=resultat.jetons_sortie,
                     duree_s=round(resultat.duree_s, 2))
        self._afficher(_c("32", f"■ RÉPONSE [{resultat.statut}, {resultat.etapes} tours] ") + resultat.texte)
