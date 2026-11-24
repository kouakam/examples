"""Recherche par mots clés, volontairement simple.

En production, on la remplacerait par un index vectoriel ou hybride
(BM25 + plongements) ; l'interface de l'outil resterait la même.
"""

from __future__ import annotations

import re
import unicodedata


def mots(texte: str) -> set[str]:
    sans_accents = unicodedata.normalize("NFKD", texte.lower()).encode("ascii", "ignore").decode()
    return {m for m in re.findall(r"[a-z0-9]+", sans_accents) if len(m) > 2}


def rechercher(documents: list[dict], requete: str, champs: tuple[str, ...], n: int = 3) -> list[dict]:
    """Note = mots communs ; un mot présent dans le premier champ (le titre) compte double."""
    cible = mots(requete)
    notes = []
    for doc in documents:
        note = 0
        for rang, champ in enumerate(champs):
            valeur = doc.get(champ, "")
            vocabulaire: set[str] = set()
            for v in valeur if isinstance(valeur, list) else [valeur]:
                vocabulaire |= mots(str(v))
            note += len(cible & vocabulaire) * (2 if rang == 0 else 1)
        if note:
            notes.append((note, doc))
    notes.sort(key=lambda x: -x[0])
    return [doc for _, doc in notes[:n]]
