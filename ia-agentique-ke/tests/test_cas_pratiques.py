"""Garde-fous de chaque cas pratique + exécution complète en mode simulation."""

import importlib

import pytest

from noyau import ErreurOutil
from noyau.cli import lancer


def test_cas1_garde_fou_remboursement():
    from cas1_service_client.outils import Etat
    e = Etat()
    with pytest.raises(ErreurOutil, match="hors mandat"):
        e.rembourser("T-03", "CMD-1003", 40_000, "geste")  # client sensible
    with pytest.raises(ErreurOutil, match="hors mandat"):
        e.rembourser("T-01", "CMD-1001", 60_000, "x")  # au-delà du seuil de 50 000 FCFA
    with pytest.raises(ErreurOutil, match="n'appartient pas"):
        e.rembourser("T-01", "CMD-1002", 1_000, "x")
    assert e.rembourser("T-02", "CMD-1002", 8_000, "pièce défectueuse")["statut"] == "remboursement effectué"


def test_cas2_compte_bancaire_et_rapprochement():
    from cas2_finance.outils import Etat
    e = Etat()
    rap = e.rapprocher("FAC-N-0913", "BC-501", [{"article": "Tôle acier 2 mm", "quantite": 100, "prix_unitaire": 12576}])
    assert rap["conforme"] is False and rap["lignes"][0]["ecart_prix_pct"] == 4.8
    with pytest.raises(ErreurOutil, match="non approuvé"):
        e.preparer_ecriture("FAC-N-0913", "F-01", 1_257_600, 242_088, 1_499_688, "CM21 10005 00001 12345678901 23")
    e.rapprocher("FAC-A-7795", "BC-504", [{"article": "Ruban adhésif 48 mm", "quantite": 200, "prix_unitaire": 1500}])
    with pytest.raises(ErreurOutil, match="fraude"):
        e.preparer_ecriture("FAC-A-7795", "F-02", 300_000, 57_750, 357_750, "CM21 40021 99001 55512345678 07")


def test_cas3_acces_sensible_impose_l_approbation():
    from cas3_rh.outils import Etat
    with pytest.raises(ErreurOutil, match="sensible"):
        Etat().demander_acces_ti("E-01", "ERP module comptabilité", "x")


def test_cas4_bac_a_sable():
    from cas4_dev.outils import Etat
    e = Etat()
    e.lire_ticket("DEV-101")
    with pytest.raises(ErreurOutil, match="interdit"):
        e.lire_fichier("../../../noyau/agent.py")
    with pytest.raises(ErreurOutil, match="tests doit passer"):
        e.ouvrir_demande_fusion("titre", "description")


def test_cas5_validation_acheteur():
    from cas5_approvisionnement.outils import Etat
    e = Etat()
    assert e.creer_demande_achat("SKU-118", "Import Asia Trading", 500, "x")["statut"].startswith("en attente")
    assert e.creer_demande_achat("SKU-310", "Textiles Sécurité Cameroun", 100, "x")["statut"] == "émise au fournisseur"
    prevision = e.prevision_demande("SKU-310", 14)
    assert prevision["tendance_hebdo"] > 0 and prevision["demande_horizon"] > 150


def test_cas6_consentement():
    from cas6_ventes.outils import Etat
    with pytest.raises(ErreurOutil, match="consentement"):
        Etat().rediger_brouillon("P-03", "objet", "corps")


def test_cas7_donnees_non_fiables_isolees():
    from cas7_secops.outils import Etat
    alerte = Etat().lire_alerte("AL-04")
    assert "ASSISTANT IA" in alerte["donnees_non_fiables"]
    assert "details" not in alerte


ATTENDUS = {
    "cas1_service_client": {"T-01": "repondre_client", "T-02": "rembourser", "T-03": "escalader", "T-05": "escalader"},
    "cas2_finance": {"FAC-A-7781": "preparer_ecriture", "FAC-A-7795": "bloquer_facture",
                     "FAC-L-2207": "bloquer_facture", "FAC-N-0913": "demander_approbation_ecart"},
    "cas3_rh": {"E-01": "demander_acces_sensible", "Q-03": "transmettre_rh"},
    "cas4_dev": {"DEV-101": "ouvrir_demande_fusion", "DEV-102": "ouvrir_demande_fusion"},
    "cas5_approvisionnement": {"NUIT": "creer_demande_achat"},
    "cas6_ventes": {"P-01": "rediger_brouillon", "P-03": "mettre_a_jour_crm"},
    "cas7_secops": {"AL-01": "bloquer_compte", "AL-02": "isoler_poste", "AL-04": "creer_incident"},
}


@pytest.mark.parametrize("module", sorted(ATTENDUS))
def test_execution_complete_en_simulation(module, capsys):
    m = importlib.import_module(f"{module}.agent")
    m.ETAT = type(m.ETAT)()  # état neuf
    resultats = dict(lancer(module, module, m.construire, m.CAS, m.politique_simulee,
                            argv=["--simulation", "--silencieux", "--auto-approuver"]))
    assert all(r.statut == "termine" for r in resultats.values())
    for identifiant, outil in ATTENDUS[module].items():
        assert outil in [a["outil"] for a in resultats[identifiant].appels_outils], identifiant
    if module == "cas7_secops":
        incident = next(i for i in m.ETAT.incidents if i["alerte_id"] == "AL-04")
        assert incident["classification"] == "incident" and "ignorée" in incident["rapport"]
