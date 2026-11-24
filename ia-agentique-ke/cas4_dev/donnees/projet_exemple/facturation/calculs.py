"""Calculs de facturation de Distribution Boréal (projet d'exemple)."""

TAUX_TVA = 0.1925


def montant_tva(montant_ht: int) -> int:
    """TVA arrondie au franc CFA le plus proche."""
    return round(montant_ht * TAUX_TVA)


def montant_ttc(montant_ht: int) -> int:
    return montant_ht + montant_tva(montant_ht)


def appliquer_remise(montant: int, pourcentage: float) -> int:
    """Renvoie le montant après remise, arrondi au franc CFA."""
    return round(montant * pourcentage / 100)


def total_commande(lignes: list[dict], remise_pct: float = 0) -> dict:
    """lignes : [{"quantite": int, "prix_unitaire": int}, ...]"""
    ht = sum(l["quantite"] * l["prix_unitaire"] for l in lignes)
    ht = appliquer_remise(ht, remise_pct) if remise_pct else ht
    return {"ht": ht, "tva": montant_tva(ht), "ttc": montant_ttc(ht)}
