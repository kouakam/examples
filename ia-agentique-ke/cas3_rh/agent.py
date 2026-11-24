"""Cas 3 · Ressources humaines — agent d'intégration des nouveaux employés.

Exécution :
    python -m cas3_rh.agent                       # avec l'API Anthropic
    python -m cas3_rh.agent --simulation          # sans clé d'API
    python -m cas3_rh.agent --simulation --auto-approuver --id E-01
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from noyau import Agent, Appel, Fin, Historique, Parallele
from noyau.cli import afficher_json, lancer

from .outils import Etat, construire_outils

SYSTEME = """Tu es l'agent d'intégration RH de Distribution Boréal.

Pour une NOUVELLE EMBAUCHE : lis le dossier, récupère le modèle du poste, puis
- crée les accès standard (demander_acces_ti) et les accès sensibles (demander_acces_sensible) ;
- commande le matériel et inscris l'employé à chaque formation du modèle ;
- envoie au gestionnaire un récapitulatif (accès, matériel, formations avec dates) ;
- signale tout élément impossible (session manquante, accès refusé).

Pour une QUESTION d'employé : cherche la politique applicable et réponds en la citant
(notifier l'employé). Toute question sur la rémunération, le contrat, l'évaluation ou un
conflit est transmise au service RH (transmettre_rh) sans donner d'avis ni de chiffre.

Ne divulgue jamais d'information sur un autre employé. Termine par un bilan en deux phrases."""

ETAT = Etat()


def construire(client=None, approbateur=None, journal=None, max_etapes=20) -> Agent:
    return Agent("cas3-rh", SYSTEME, construire_outils(ETAT), client=client,
                 approbateur=approbateur, journal=journal, max_etapes=max(max_etapes, 20))


CAS = ([(e, f"Prépare l'intégration de la nouvelle embauche {e}.") for e in ETAT.embauches]
       + [(q, f"Réponds à la question d'employé {q}.") for q in ETAT.questions])


# --------------------------------------------------------------- simulation
def _integration(employe_id: str, h: Historique):
    if not h.a_appele("lire_dossier_embauche"):
        return Appel("lire_dossier_embauche", {"employe_id": employe_id})
    dossier = h.resultat("lire_dossier_embauche")
    if not h.a_appele("obtenir_modele_integration"):
        return Appel("obtenir_modele_integration", {"poste": dossier["poste"]})
    modele = h.resultat("obtenir_modele_integration")
    if not h.a_appele("demander_acces_ti"):
        return Parallele([Appel("demander_acces_ti" if not a["sensible"] else "demander_acces_sensible",
                                {"employe_id": employe_id, "systeme": a["systeme"],
                                 "justification": f"Modèle d'intégration du poste {dossier['poste']}"})
                          for a in modele["acces"]]
                         + [Appel("commander_materiel", {"employe_id": employe_id, "articles": modele["materiel"]})]
                         + [Appel("planifier_formation", {"employe_id": employe_id, "formation": f})
                            for f in modele["formations"]],
                         "Je lance en parallèle les accès, le matériel et les formations.")
    if not h.a_appele("notifier"):
        formations = [f"{x['entree']['formation']} : " + (x["resultat"]["date"] if not x["erreur"] else "AUCUNE SESSION")
                      for x in h.appels("planifier_formation")]
        acces = [f"{x['entree']['systeme']} ({'refusé' if 'refusé' in str(x['resultat']) else 'demandé'})"
                 for x in h.appels("demander_acces_ti") + h.appels("demander_acces_sensible")]
        return Appel("notifier", {"destinataire": dossier["courriel_gestionnaire"],
                                  "objet": f"Intégration de {dossier['nom']} le {dossier['date_arrivee']}",
                                  "message": "Accès : " + "; ".join(acces) + ". Formations : "
                                             + "; ".join(formations) + "."})
    return Fin(f"Intégration de {dossier['nom']} préparée ; récapitulatif envoyé à {dossier['gestionnaire']}.")


def _question(question_id: str, h: Historique):
    if not h.a_appele("lire_question"):
        return Appel("lire_question", {"question_id": question_id})
    q = h.resultat("lire_question")
    if not h.a_appele("chercher_politiques_rh"):
        return Appel("chercher_politiques_rh", {"requete": q["question"]})
    if h.a_appele("transmettre_rh") or h.a_appele("notifier"):
        return Fin(f"Question {question_id} traitée.")
    politiques = h.resultat("chercher_politiques_rh")
    politique = politiques[0]
    if any(p["id"] == "POL-05" for p in politiques):  # tout signal de rémunération → RH
        return Appel("transmettre_rh", {"employe_id": q["employe_id"], "sujet": q["question"],
                                        "motif": "Rémunération individuelle : hors périmètre de l'agent."})
    return Appel("notifier", {"destinataire": q["employe"]["nom"], "objet": politique["titre"],
                              "message": f"Bonjour, selon la politique « {politique['titre']} » : {politique['texte']}"})


def politique_simulee(demande: str, h: Historique):
    if m := re.search(r"E-\d+", demande):
        return _integration(m.group(), h)
    return _question(re.search(r"Q-\d+", demande).group(), h)


def bilan() -> None:
    afficher_json("Actions d'intégration", ETAT.bilan())
    sortie = Path(__file__).resolve().parent.parent / "sortie" / "cas3_bilan.json"
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(json.dumps(ETAT.bilan(), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    lancer("cas3", "Cas 3 · Agent d'intégration RH", construire, CAS, politique_simulee, bilan)
