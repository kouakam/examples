"""Cas 4 · Génie logiciel — outils de l'agent de code.

Chaque ticket est traité dans une COPIE du projet (bac à sable), sous
`sortie/cas4/<ticket>/`. L'agent ne peut ni sortir de ce dossier, ni écrire
autre chose que du code source ou des tests, ni ouvrir une demande de
fusion tant que la suite de tests ne passe pas. La fusion reste humaine.

Attention : executer_tests lance du code Python écrit par l'agent. En
production, ce bac à sable serait un conteneur isolé sans accès réseau.
"""

from __future__ import annotations

import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from noyau import ErreurOutil, Outil

DOSSIER = Path(__file__).parent / "donnees"
PROJET = DOSSIER / "projet_exemple"
SORTIE = Path(__file__).resolve().parent.parent / "sortie" / "cas4"
EXTENSIONS_AUTORISEES = {".py", ".md", ".txt"}
IGNORES = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")


class Etat:
    def __init__(self):
        self.tickets = {t["id"]: t for t in json.loads((DOSSIER / "tickets.json").read_text(encoding="utf-8"))}
        self.ticket: dict | None = None
        self.espace: Path | None = None
        self.derniers_tests: dict | None = None
        self.demandes_fusion: list[dict] = []

    # ------------------------------------------------------------ bac à sable
    def _chemin(self, chemin: str) -> Path:
        if self.espace is None:
            raise ErreurOutil("Aucun ticket ouvert : appelez d'abord lire_ticket.")
        cible = (self.espace / chemin).resolve()
        if not cible.is_relative_to(self.espace.resolve()):
            raise ErreurOutil("Chemin interdit : hors de l'espace de travail.")
        return cible

    def _fichiers(self, racine: Path) -> list[str]:
        return sorted(str(p.relative_to(racine)) for p in racine.rglob("*")
                      if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts)

    # ------------------------------------------------------------ outils
    def lire_ticket(self, ticket_id: str) -> dict:
        if ticket_id not in self.tickets:
            raise ErreurOutil(f"Ticket {ticket_id} introuvable.")
        self.ticket = self.tickets[ticket_id]
        self.espace = SORTIE / ticket_id
        if self.espace.exists():
            shutil.rmtree(self.espace)
        shutil.copytree(PROJET, self.espace, ignore=IGNORES)
        self.derniers_tests = None
        return {**self.ticket, "espace_de_travail": "copie fraîche du projet créée"}

    def lister_fichiers(self) -> list[str]:
        return self._fichiers(self._chemin("."))

    def lire_fichier(self, chemin: str) -> str:
        cible = self._chemin(chemin)
        if not cible.is_file():
            raise ErreurOutil(f"Fichier introuvable : {chemin}")
        return cible.read_text(encoding="utf-8")

    def remplacer_dans_fichier(self, chemin: str, ancien: str, nouveau: str) -> dict:
        cible = self._chemin(chemin)
        texte = self.lire_fichier(chemin)
        occurrences = texte.count(ancien)
        if occurrences != 1:
            raise ErreurOutil(f"Le texte à remplacer apparaît {occurrences} fois (il doit être unique).")
        cible.write_text(texte.replace(ancien, nouveau), encoding="utf-8")
        return {"statut": "modifié", "chemin": chemin}

    def ecrire_fichier(self, chemin: str, contenu: str) -> dict:
        cible = self._chemin(chemin)
        if cible.suffix not in EXTENSIONS_AUTORISEES:
            raise ErreurOutil(f"Extension non autorisée : {cible.suffix}")
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")
        return {"statut": "écrit", "chemin": chemin, "lignes": contenu.count("\n") + 1}

    def executer_tests(self) -> dict:
        espace = self._chemin(".")
        try:
            proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                                  cwd=espace, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            raise ErreurOutil("Tests interrompus après 120 s (boucle infinie ?).")
        sortie = (proc.stdout + proc.stderr).strip().splitlines()
        self.derniers_tests = {"reussi": proc.returncode == 0, "code_retour": proc.returncode,
                               "sortie": "\n".join(sortie[-40:])}
        return self.derniers_tests

    def ouvrir_demande_fusion(self, titre: str, description: str) -> dict:
        if not self.derniers_tests or not self.derniers_tests["reussi"]:
            raise ErreurOutil("Impossible : la suite de tests doit passer juste avant l'ouverture.")
        espace = self._chemin(".")
        diff: list[str] = []
        for rel in sorted(set(self._fichiers(PROJET)) | set(self._fichiers(espace))):
            avant = (PROJET / rel).read_text(encoding="utf-8").splitlines(True) if (PROJET / rel).exists() else []
            apres = (espace / rel).read_text(encoding="utf-8").splitlines(True) if (espace / rel).exists() else []
            diff += difflib.unified_diff(avant, apres, f"a/{rel}", f"b/{rel}")
        if not diff:
            raise ErreurOutil("Aucune modification à proposer.")
        ticket = self.ticket["id"]
        (SORTIE / f"{ticket}.diff").write_text("".join(diff), encoding="utf-8")
        (SORTIE / f"{ticket}.md").write_text(f"# {titre}\n\nTicket : {ticket}\n\n{description}\n", encoding="utf-8")
        demande = {"ticket": ticket, "titre": titre, "fichier_diff": f"sortie/cas4/{ticket}.diff",
                   "lignes_modifiees": sum(1 for l in diff if l[:1] in "+-" and l[:3] not in ("+++", "---")),
                   "statut": "ouverte, en attente de revue humaine"}
        self.demandes_fusion.append(demande)
        return demande


def construire_outils(e: Etat) -> list[Outil]:
    t = {"type": "string"}
    return [
        Outil("lire_ticket", "Lit le ticket et prépare une copie fraîche du projet (bac à sable). À appeler en premier.",
              {"ticket_id": t}, e.lire_ticket),
        Outil("lister_fichiers", "Liste les fichiers du projet.", {}, e.lister_fichiers),
        Outil("lire_fichier", "Lit un fichier du projet (chemin relatif).", {"chemin": t}, e.lire_fichier),
        Outil("remplacer_dans_fichier", "Remplace un extrait EXACT et UNIQUE d'un fichier. À préférer à la réécriture.",
              {"chemin": t, "ancien": t, "nouveau": t}, e.remplacer_dans_fichier),
        Outil("ecrire_fichier", "Crée ou réécrit un fichier (.py, .md, .txt), par exemple un nouveau fichier de test.",
              {"chemin": t, "contenu": t}, e.ecrire_fichier),
        Outil("executer_tests", "Exécute toute la suite pytest du projet et renvoie le résultat.", {}, e.executer_tests),
        Outil("ouvrir_demande_fusion", "Ouvre une demande de fusion avec le diff. Seulement si les tests passent. "
              "La description explique la cause, la correction et les tests ajoutés.",
              {"titre": t, "description": t}, e.ouvrir_demande_fusion),
    ]
