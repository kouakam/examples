"""Exécute les sept cas pratiques à la suite.

    python tout_executer.py --simulation --auto-approuver   # sans clé d'API
    python tout_executer.py --auto-refuser                   # agents réels, actions sensibles refusées
Les options sont transmises à chaque cas (voir noyau/cli.py).
"""

import importlib
import sys

MODULES = ["cas1_service_client", "cas2_finance", "cas3_rh", "cas4_dev",
           "cas5_approvisionnement", "cas6_ventes", "cas7_secops"]

if __name__ == "__main__":
    from noyau.cli import lancer

    for nom in MODULES:
        m = importlib.import_module(f"{nom}.agent")
        print("\n" + "#" * 78)
        lancer(nom, nom, m.construire, m.CAS, m.politique_simulee, m.bilan, argv=sys.argv[1:])
