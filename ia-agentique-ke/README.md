# L’IA agentique en entreprise — code des cas pratiques

**Logiciel KE inc.** · Séminaire de maîtrise, Polytechnique Yaoundé · Décembre 2026
Présentateur : Ervée Kouakam, président de Logiciel KE inc. · logicielke.com

Ce dossier contient le code source complet et exécutable des **sept cas pratiques** de la
présentation, chacun avec un jeu de données d’exemple. Le fil rouge est *Distribution Boréal*,
un distributeur de fournitures industrielles **fictif** ; toutes les données sont inventées.

| Cas | Dossier | Ce que fait l’agent | Garde-fous illustrés |
|---|---|---|---|
| 1 · Service client | `cas1_service_client/` | Résout ou escalade 5 tickets (suivi, pièce défectueuse, réclamation agressive, question de politique, tentative de manipulation) | Seuil de remboursement codé en dur, client sensible, message client traité comme une donnée |
| 2 · Finance | `cas2_finance/` | Lit 4 factures en texte libre, rapproche facture / bon de commande / réception, prépare le lot de paiement | Rapprochement déterministe, approbation humaine des écarts, détection du doublon et de la fraude au changement de RIB |
| 3 · RH | `cas3_rh/` | Prépare l’intégration de 2 nouveaux employés et répond à 3 questions | Accès sensibles soumis au gestionnaire, rémunération transmise aux RH |
| 4 · Génie logiciel | `cas4_dev/` | Corrige un vrai bogue et ajoute une validation dans un petit projet Python, avec tests, puis produit un diff | Bac à sable, test rouge avant correction, aucune fusion sans tests au vert |
| 5 · Approvisionnement | `cas5_approvisionnement/` | Analyse 4 articles, prévoit la demande (régression), lit les signaux (grève au port, commande client) et crée les demandes d’achat | Validation de l’acheteur au-delà d’un montant ou hors fournisseur référencé |
| 6 · Ventes | `cas6_ventes/` | Qualifie 3 prospects, rédige un brouillon de courriel, met à jour le CRM | Pas de brouillon sans consentement, aucun envoi automatique |
| 7 · Cybersécurité | `cas7_secops/` | Trie 4 alertes SOC (force brute, macro malveillante, faux positif, hameçonnage) | Injection de prompt dans les données (AL-04), confinement validé par un analyste |

## 1. Installation

Prérequis : **Python 3.10 ou plus récent**.

```bash
cd ia-agentique-ke
python -m venv .venv
# Linux / macOS :
source .venv/bin/activate
# Windows (PowerShell) :
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Deux modes d’exécution

### Mode simulation : sans clé d’API, sans réseau

Une politique Python déterministe remplace le modèle. Les outils, les données, la boucle, les
approbations et les traces sont **exactement les mêmes** qu’en mode réel. Ce mode sert à vérifier
l’installation, à faire la démonstration en classe sans connexion, et à comparer un « workflow
codé à la main » avec un vrai agent (diapositive *Workflow ou agent*).

```bash
python tout_executer.py --simulation --auto-approuver     # les 7 cas d’un coup
python -m cas2_finance.agent --simulation                 # un cas, approbations demandées en console
```

### Mode réel : avec l’API Anthropic

```bash
# Linux / macOS
export ANTHROPIC_API_KEY="votre-clé"
# Windows (PowerShell)
# $env:ANTHROPIC_API_KEY="votre-clé"

python -m cas1_service_client.agent
python -m cas7_secops.agent --id AL-04         # un seul élément du jeu d’exemples
```

Par défaut, le modèle est `claude-opus-5-5`. Pour en changer, définissez la variable
`KE_MODELE`, par exemple `KE_MODELE=claude-sonnet-5-5` pour réduire le coût.

Le code active le **repli automatique côté serveur** (paramètre `fallbacks="default"`) : si le
modèle décline une requête pour des raisons de sécurité, l’API relance la même requête sur un
modèle de repli. Sur une plateforme qui ne le prend pas en charge (Amazon Bedrock, Vertex AI,
Microsoft Foundry), désactivez-le avec `KE_SANS_REPLI=1`.

> **Coût.** Le mode réel consomme des jetons facturés. Lancez d’abord un seul élément avec `--id`
> pour estimer la consommation ; la synthèse affiche les jetons utilisés par exécution.

### Options communes

| Option | Effet |
|---|---|
| `--simulation` | Exécuter sans modèle |
| `--id T-03` | N’exécuter qu’un élément du jeu d’exemples |
| `--auto-approuver` / `--auto-refuser` | Décider automatiquement des actions sensibles (sinon : question en console) |
| `--max-etapes 15` | Budget d’étapes de la boucle agentique |
| `--silencieux` | N’afficher que la synthèse |

## 3. Ce que vous obtenez

- **En console** : la trace de chaque tour (`→ tool_use`, `← tool_result`, `✋ humain`), puis une synthèse.
- **`traces/`** : un fichier JSONL par exécution (demande, appels d’outils, résultats, décisions
  humaines, jetons, durée), prêt à être chargé dans un outil d’observabilité.
- **`sortie/`** : l’état final de chaque « système » simulé (tickets, lot de paiement, demandes
  d’achat, incidents…), les brouillons de courriels (cas 6) et les diffs de demande de fusion (cas 4).

## 4. Évaluation et tests

```bash
python -m cas1_service_client.evals --simulation   # jeu d’évaluation du cas 1 (démo 6)
python -m cas1_service_client.evals --juge          # agent réel + LLM-juge (claude-sonnet-5-5)
python -m pytest                                    # 23 tests, sans réseau
```

Les tests couvrent la boucle agentique (erreurs d’outils, refus, budget, appels parallèles),
les garde-fous de chaque cas, l’exécution complète des 7 cas en simulation, et le chemin réel
avec le vrai SDK Anthropic branché sur un faux serveur HTTP.

## 5. Structure du code

```
noyau/                  boucle agentique commune
  agent.py              Agent, Outil, approbation humaine, gestion des stop_reason
  simulation.py         client simulé (même interface que le SDK)
  journal.py            trace console + JSONL
  recherche.py          recherche par mots clés (à remplacer par un index vectoriel)
  cli.py                options en ligne de commande communes
casN_xxx/
  donnees/              jeu d’exemples (JSON, CSV, texte)
  outils.py             fonctions métier + schémas d’outils (mode strict)
  agent.py              invite système, construction de l’agent, politique de simulation
tests/                  tests automatisés
tout_executer.py        lance les sept cas
```

Pour ajouter un cas : copiez un dossier existant, remplacez les données, écrivez les fonctions
de `outils.py`, puis adaptez l’invite système de `agent.py`.

## 6. Passer à un vrai système d’information

Chaque fonction de `outils.py` lit aujourd’hui un fichier JSON. Pour une intégration réelle,
remplacez son corps par l’appel au système concerné (ERP, CRM, SIRH, SIEM…) **sans changer son
nom, sa description ni son schéma** : l’agent fonctionnera à l’identique. En production, ajoutez :
authentification et permissions par rôle (idéalement via un serveur MCP, voir la démo 2), bac à
sable isolé pour le cas 4, stockage persistant des états, et la validation humaine dans vos outils
habituels (Teams, courriel, application web) à la place de la console.

## 7. Limites connues

- En mode simulation, les décisions viennent de règles écrites à la main. Le cas 4 contient
  des correctifs préenregistrés ; seul un vrai modèle les écrit lui-même.
- `executer_tests` (cas 4) exécute du code Python écrit par l’agent dans `sortie/cas4/`. Lancez ce
  cas dans un conteneur ou une machine de test.
- Le comportement exact du modèle réel varie d’une exécution à l’autre : c’est pourquoi on
  l’évalue sur un jeu de cas (`evals.py`) plutôt que sur un seul exemple.
