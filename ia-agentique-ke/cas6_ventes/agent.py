"""Cas 6 · Ventes — qualification de prospects et préparation de rendez-vous.

Exécution :
    python -m cas6_ventes.agent                  # avec l'API Anthropic
    python -m cas6_ventes.agent --simulation     # sans clé d'API
Brouillons : sortie/cas6/brouillon_<prospect>.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from noyau import Agent, Appel, Fin, Historique, Parallele
from noyau.cli import afficher_json, lancer

from .outils import Etat, construire_outils

SYSTEME = """Tu assistes l'équipe commerciale de Distribution Boréal. Pour chaque prospect :
1. Lis la fiche, le profil client idéal et l'historique CRM ; recherche l'entreprise.
2. Attribue un score d'adéquation de 0 à 100, justifié par des faits sourcés (secteur, taille,
   signaux d'achat). N'invente aucun fait ; écris « non trouvé » si l'information manque.
3. Si le score est d'au moins 60 ET que le prospect a consenti à la prospection, rédige un
   brouillon de premier courriel court et personnalisé (aucun envoi automatique).
4. Mets toujours le CRM à jour : score, note de préparation, prochaine étape.
Ne collecte pas d'informations personnelles au-delà du contact professionnel indiqué.
Termine par une recommandation d'une phrase pour le commercial."""

ETAT = Etat()


def construire(client=None, approbateur=None, journal=None, max_etapes=15) -> Agent:
    return Agent("cas6-ventes", SYSTEME, construire_outils(ETAT), client=client,
                 approbateur=approbateur, journal=journal, max_etapes=max_etapes)


CAS = [(p, f"Qualifie le prospect {p} et prépare la prise de contact.") for p in ETAT.prospects]

SECTEURS_CIBLES = ("industrie", "agroalimentaire", "minière", "mines", "extraction", "btp", "production", "maintenance")


def _effectif(textes: str) -> int:
    nombres = [int(n.replace(" ", "")) for n in re.findall(r"(\d[\d ]*\d|\d+)\s*(?:personnes|salariés)", textes)]
    return max(nombres, default=0)


def politique_simulee(demande: str, h: Historique):
    pid = re.search(r"P-\d+", demande).group()
    if not h.a_appele("lire_prospect"):
        return Appel("lire_prospect", {"prospect_id": pid})
    p = h.resultat("lire_prospect")
    if not h.a_appele("rechercher_web"):
        return Parallele([Appel("lire_profil_client_ideal", {}), Appel("lire_crm", {"entreprise": p["entreprise"]}),
                          Appel("rechercher_web", {"requete": p["entreprise"]})])
    infos = [r for r in h.resultat("rechercher_web") if "texte" in r]
    textes = " ".join(r["texte"] + " " + r["titre"] for r in infos).lower()
    effectif = _effectif(textes)
    secteur = any(s in textes for s in SECTEURS_CIBLES)
    signaux = [s for s in ("nouvelle ligne", "nouveau site", "recrutement", "iso 45001", "renouveler") if s in textes]
    score = (40 if secteur else 0) + (25 if effectif > 50 else 0) + min(35, 12 * len(signaux))
    if not h.a_appele("rediger_brouillon") and score >= 60 and p["consentement_prospection"]:
        actu = infos[0]["titre"] if infos else ""
        return Appel("rediger_brouillon", {
            "prospect_id": pid, "objet": f"{p['entreprise']} : vos équipements de protection et pièces de maintenance",
            "corps": f"Bonjour {p['contact'].split(',')[0]},\n\nMerci pour votre demande. Nous avons lu que « {actu} ». "
                     "Distribution Boréal accompagne déjà plusieurs sites industriels du Littoral et du Centre pour "
                     "leurs EPI et consommables de maintenance, avec livraison sous 48 h.\n\nSeriez-vous disponible "
                     "pour un échange de 20 minutes la semaine prochaine ?\n\n[Signature du commercial]"})
    if not h.a_appele("mettre_a_jour_crm"):
        historique = h.resultat("lire_crm").get("historique", [])
        etape = ("Appel de qualification par le commercial sous 48 h" if score >= 60 and p["consentement_prospection"]
                 else "Ne pas contacter : consentement absent, vérifier une base légale" if not p["consentement_prospection"]
                 else "Hors cible : archiver")
        return Appel("mettre_a_jour_crm", {
            "prospect_id": pid, "score": score, "prochaine_etape": etape,
            "note": f"Secteur cible : {'oui' if secteur else 'non'} ; effectif : {effectif or 'non trouvé'} ; "
                    f"signaux : {', '.join(signaux) or 'aucun'} ; historique CRM : "
                    f"{historique[-1]['note'] if historique else 'aucun'}."})
    return Fin(f"{p['entreprise']} : score {score}/100. {h.resultat('mettre_a_jour_crm')['prochaine_etape']}.")


def bilan() -> None:
    afficher_json("CRM et brouillons", ETAT.bilan())
    sortie = Path(__file__).resolve().parent.parent / "sortie" / "cas6_bilan.json"
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(json.dumps(ETAT.bilan(), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    lancer("cas6", "Cas 6 · Agent de qualification commerciale", construire, CAS, politique_simulee, bilan)
