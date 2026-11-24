from facturation.calculs import montant_tva, montant_ttc, total_commande


def test_tva():
    assert montant_tva(100_000) == 19_250


def test_ttc():
    assert montant_ttc(100_000) == 119_250


def test_total_sans_remise():
    lignes = [{"quantite": 2, "prix_unitaire": 10_000}, {"quantite": 1, "prix_unitaire": 5_000}]
    assert total_commande(lignes) == {"ht": 25_000, "tva": 4_812, "ttc": 29_812}
