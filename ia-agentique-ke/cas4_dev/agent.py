"""Cas 4 · Génie logiciel — agent de code : du ticket à la demande de fusion.

Exécution :
    python -m cas4_dev.agent                 # avec l'API Anthropic
    python -m cas4_dev.agent --simulation    # sans clé d'API (correctifs préenregistrés)
Résultats : sortie/cas4/<ticket>.diff et <ticket>.md
"""

from __future__ import annotations

import re

from noyau import Agent, Appel, Fin, Historique
from noyau.cli import afficher_json, lancer

from .outils import Etat, construire_outils

SYSTEME = """Tu es un agent de génie logiciel chez Distribution Boréal. Tu traites un ticket
dans un bac à sable contenant une copie du projet Python.

Méthode obligatoire :
1. Lis le ticket, liste les fichiers, lis le code et les tests concernés.
2. Pour un bogue : écris D'ABORD un test qui reproduit le problème et vérifie qu'il échoue.
3. Corrige avec la modification la plus petite possible (remplacer_dans_fichier).
4. Exécute toute la suite de tests ; itère jusqu'à ce qu'elle passe (au plus 3 tentatives).
5. Ouvre une demande de fusion : cause, correction, tests ajoutés.
Ne modifie jamais un test existant pour le faire passer. Si tu n'y arrives pas, explique
pourquoi au lieu d'ouvrir une demande de fusion."""

ETAT = Etat()


def construire(client=None, approbateur=None, journal=None, max_etapes=25) -> Agent:
    return Agent("cas4-dev", SYSTEME, construire_outils(ETAT), client=client,
                 approbateur=approbateur, journal=journal, max_etapes=max(max_etapes, 25))


CAS = [(t, f"Traite le ticket {t}.") for t in ETAT.tickets]

# --------------------------------------------------------------- simulation
# En mode simulation, les correctifs sont préenregistrés : seul un vrai
# modèle sait les écrire. Le déroulement (test rouge, correction, test vert,
# demande de fusion) est en revanche identique.
TEST_101 = '''from facturation.calculs import appliquer_remise, total_commande


def test_remise_10_pourcent():
    assert appliquer_remise(50_000, 10) == 45_000


def test_total_avec_remise():
    assert total_commande([{"quantite": 1, "prix_unitaire": 50_000}], remise_pct=10)["ht"] == 45_000
'''
TEST_102 = '''import pytest

from facturation.calculs import appliquer_remise


@pytest.mark.parametrize("pourcentage", [-5, 100.5, 150])
def test_pourcentage_invalide(pourcentage):
    with pytest.raises(ValueError):
        appliquer_remise(10_000, pourcentage)


@pytest.mark.parametrize("pourcentage", [0, 50, 100])
def test_bornes_valides(pourcentage):
    appliquer_remise(10_000, pourcentage)  # ne doit pas lever d'exception
'''
CORRECTIFS = {
    "DEV-101": ("tests/test_remise.py", TEST_101,
                "    return round(montant * pourcentage / 100)",
                "    return round(montant * (1 - pourcentage / 100))"),
    "DEV-102": ("tests/test_validation_remise.py", TEST_102,
                '    """Renvoie le montant après remise, arrondi au franc CFA."""\n',
                '    """Renvoie le montant après remise, arrondi au franc CFA."""\n'
                '    if not 0 <= pourcentage <= 100:\n'
                '        raise ValueError(f"Pourcentage de remise invalide : {pourcentage}")\n'),
}


def politique_simulee(demande: str, h: Historique):
    ticket = re.search(r"DEV-\d+", demande).group()
    fichier_test, test, ancien, nouveau = CORRECTIFS[ticket]
    if not h.a_appele("lire_ticket"):
        return Appel("lire_ticket", {"ticket_id": ticket})
    if not h.a_appele("lister_fichiers"):
        return Appel("lister_fichiers", {})
    if not h.a_appele("lire_fichier"):
        return Appel("lire_fichier", {"chemin": "facturation/calculs.py"})
    if not h.a_appele("ecrire_fichier"):
        return Appel("ecrire_fichier", {"chemin": fichier_test, "contenu": test},
                     "J'écris d'abord un test qui reproduit le problème.")
    tests = h.appels("executer_tests")
    if not tests:
        return Appel("executer_tests", {})
    if not h.a_appele("remplacer_dans_fichier"):
        if ticket == "DEV-102" or not tests[-1]["resultat"]["reussi"]:
            return Appel("remplacer_dans_fichier", {"chemin": "facturation/calculs.py",
                                                    "ancien": ancien, "nouveau": nouveau},
                         "Le test échoue comme prévu ; j'applique la correction minimale.")
    if len(tests) < 2:
        return Appel("executer_tests", {})
    if not tests[-1]["resultat"]["reussi"]:
        return Fin("Les tests échouent encore : pas de demande de fusion, analyse humaine requise.")
    if not h.a_appele("ouvrir_demande_fusion"):
        return Appel("ouvrir_demande_fusion", {
            "titre": f"{ticket} : {ETAT.tickets[ticket]['titre']}",
            "description": f"Correction : `{nouveau.strip()}`. Test ajouté : {fichier_test}. Suite complète au vert."})
    return Fin(f"Demande de fusion ouverte pour {ticket} ; en attente de revue humaine.")


def bilan() -> None:
    afficher_json("Demandes de fusion", ETAT.demandes_fusion)


if __name__ == "__main__":
    lancer("cas4", "Cas 4 · Agent de code", construire, CAS, politique_simulee, bilan)
