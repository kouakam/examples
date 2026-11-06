# Plateforme intégrée de gestion immobilière — Stack technique

> Complète `SPECIFICATIONS_FONCTIONNELLES.md` et les maquettes d'écran.
> Version 1.0 — novembre 2026

---

## 1. Principes qui guident les choix

| Contrainte métier | Conséquence technique |
|---|---|
| L'argent des propriétaires transite par la plateforme | Base relationnelle transactionnelle (ACID), grand livre en partie double, écritures non modifiables, montants en entiers |
| Transparence et traçabilité | Journal d'audit en ajout seul, horodatage, pièce justificative attachée à chaque mouvement |
| Utilisateurs sur téléphone, réseau 3G parfois instable | Applications mobiles hors-ligne, pages légères, images compressées, SMS/USSD en secours |
| Paiement mobile money (Orange Money, MTN MoMo) | Couche paiement découplée, multi-fournisseurs, rapprochement automatique |
| Équipe de démarrage réduite | **Monolithe modulaire** plutôt que microservices ; un seul langage de bout en bout |
| Croissance multi-agences, multi-pays | Multi-locataire dès le départ, règles métier paramétrables par pays |
| Charte Quitus déjà conçue pour Angular | Réutiliser la charte et ses composants côté web et mobile |

---

## 2. Vue d'ensemble

```
            ┌──────────────── Clients ────────────────┐
            │ Web (Angular)  ·  Apps mobiles (Ionic/  │
            │ Capacitor)  ·  Site vitrine (Angular SSR)│
            │ API partenaires  ·  Webhooks  ·  USSD/SMS│
            └───────────────────┬─────────────────────┘
                                │ HTTPS
                ┌───────────────▼────────────────┐
                │ Passerelle : WAF + équilibreur │
                │ + limitation de débit          │
                └───────────────┬────────────────┘
                                │
   ┌────────────────────────────▼────────────────────────────┐
   │ Backend NestJS (TypeScript) — monolithe modulaire        │
   │  Patrimoine · Mandats · Location · Saisonnier · Vente ·  │
   │  Terrains · Comptabilité · Paiements · Travaux · CRM ·   │
   │  Documents · Contentieux · Reporting · Notifications     │
   │  API REST (OpenAPI)  ·  Workers (files de tâches)        │
   └──┬───────────┬───────────┬───────────┬───────────┬──────┘
      │           │           │           │           │
 PostgreSQL    Redis      Stockage     Moteur de    Keycloak
 + PostGIS   (cache,      objet S3     recherche    (identité,
 (données,   files de     (documents,  (annonces)   MFA, SSO)
  grand      tâches)      photos)
  livre)
      │
  Réplique en lecture → BI (Metabase) et exports
```

---

## 3. Choix recommandés, couche par couche

### 3.1 Front web (back-office, espaces propriétaire et partenaire)
| Élément | Choix | Pourquoi |
|---|---|---|
| Framework | **Angular** (dernière version stable, composants autonomes, signaux) | La charte Quitus et ses composants (`lucide-angular`) sont déjà prévus pour Angular |
| Interface | Charte **Quitus** (jetons de couleur, Sora/Inter) + Angular CDK pour tableaux, fenêtres, glisser-déposer | Cohérence avec les maquettes |
| État | Signaux Angular + NgRx Signal Store pour les écrans complexes | Simple et performant |
| Tableaux de données | AG Grid (version communautaire) pour le back-office | Tri, filtres, export, gros volumes |
| Graphiques | Apache ECharts | Tableaux de bord, rendement, occupation |
| Cartes | **MapLibre GL** + tuiles OpenStreetMap | Carte du patrimoine, plan des lotissements, pas de coût de licence |
| Formulaires | Reactive Forms + validation partagée avec le backend (schémas Zod générés depuis OpenAPI) | Une seule source de règles |
| Internationalisation | Angular i18n (FR par défaut, EN) | Marché bilingue |

### 3.2 Site vitrine et annonces
- **Angular SSR** (rendu côté serveur) pour le référencement des annonces et des pages agences.
- Images servies par un CDN, redimensionnées à la volée (formats WebP/AVIF).

### 3.3 Applications mobiles (propriétaire, locataire, gestionnaire terrain, prestataire)
| Élément | Choix | Pourquoi |
|---|---|---|
| Framework | **Ionic + Capacitor** (Angular) | Même code, mêmes composants et même équipe que le web ; une app iOS + Android |
| Hors-ligne | SQLite (plugin Capacitor) + file de synchronisation | États des lieux et visites sans réseau |
| Photos | Plugin caméra, compression avant envoi, envoi différé | Économie de données mobiles |
| Notifications | Firebase Cloud Messaging (Android et iOS) | Standard, gratuit |
| Signature sur écran | Canvas de signature + horodatage serveur | EDL et bons de visite |
| PWA | Version web installable pour les locataires qui ne veulent pas d'application | Accès sans téléchargement |

> Alternative si l'équipe est plutôt mobile : **Flutter**. Mais deux bases de code d'interface (Angular et Flutter) coûtent plus cher à maintenir.

### 3.4 Backend
| Élément | Choix | Pourquoi |
|---|---|---|
| Langage | **TypeScript** sur Node.js LTS | Même langage que le front, recrutement facile |
| Framework | **NestJS** | Modules, injection de dépendances, structure claire pour un monolithe modulaire |
| Architecture | Monolithe modulaire, un module par domaine métier (chaque module de la spécification), frontières strictes, communication par événements internes | Livrer vite, découper plus tard si besoin |
| Accès aux données | **Prisma** (ou Drizzle) + SQL brut pour la comptabilité | Typage fort ; requêtes comptables maîtrisées |
| API | REST + **OpenAPI** générée, versionnée (`/v1`) ; webhooks signés pour partenaires | Simple à intégrer pour les partenaires |
| Tâches de fond | **BullMQ** sur Redis | Quittancement de masse, relances, révisions de loyer, reversements, génération de PDF |
| Planification | Tâches planifiées BullMQ (cron) | Calendrier de gestion automatisé |
| Événements | Pattern « outbox » en base, puis bus interne | Fiabilité : aucun événement perdu si un service tombe |
| Moteur de règles | Règles paramétrables en base (indices, délais de préavis, honoraires, plafonds) par pays | Pas de réglementation codée en dur |
| Workflows | Moteur de workflows maison simple au départ ; **Temporal** si les processus longs se multiplient (vente, contentieux) | Processus de plusieurs semaines fiables |

> Alternative si l'équipe est C# (charte PES Blazor) : **ASP.NET Core** + Entity Framework Core. Les autres choix restent valables.

### 3.5 Données
| Élément | Choix | Usage |
|---|---|---|
| Base principale | **PostgreSQL** (géré) | Toutes les données métier |
| Géographie | **PostGIS** | Parcelles, bornes GPS, lotissements, recherche par zone |
| Multi-locataire | Colonne `tenant_id` + **Row-Level Security** PostgreSQL | Cloisonnement des agences et partenaires garanti par la base |
| Grand livre | Tables d'écritures en ajout seul (pas de mise à jour ni suppression, corrections par contre-passation), contrôle d'équilibre par transaction | Comptabilité du propriétaire fiable et auditable |
| Montants | Entiers en plus petite unité + code devise (XAF, EUR, CAD…) | Jamais de nombres à virgule flottante pour l'argent |
| Audit | Table d'audit en ajout seul + chaînage par empreinte (hash) | Preuve d'intégrité |
| Cache et sessions | **Redis** | Performance |
| Recherche | **Meilisearch** (ou OpenSearch à grande échelle) | Recherche d'annonces, de lots, de tiers |
| Analytique | Réplique en lecture → **Metabase** ; entrepôt (ClickHouse ou BigQuery) en V3 | Tableaux de bord sans charger la base principale |
| Sauvegardes | pgBackRest ou sauvegardes gérées, restauration à un instant donné, copie chiffrée hors site | Plan de reprise |

### 3.6 Documents
| Élément | Choix |
|---|---|
| Stockage | Stockage objet compatible **S3** (fournisseur cloud ou MinIO), chiffré, versionné |
| Antivirus | ClamAV sur chaque fichier déposé |
| Génération PDF | Modèles HTML (Handlebars) → PDF via **Gotenberg** : baux, quittances, CRG, mises en demeure |
| OCR et extraction | Moteur OCR + modèle d'IA (voir 3.10) pour lire factures, pièces d'identité, titres fonciers |
| Signature électronique | Prestataire de signature électronique conforme au droit applicable (à valider par un juriste par pays) ; intégration par API et webhooks |
| Archivage probant | Horodatage qualifié + empreinte stockée, conservation selon durées légales |

### 3.7 Paiements
| Besoin | Choix |
|---|---|
| Mobile money | API **Orange Money** et **MTN MoMo**, ou agrégateur régional (CinetPay, Campay, Notch Pay, Flutterwave…) pour un seul contrat |
| Cartes | Via l'agrégateur ; Stripe pour les propriétaires et locataires de la diaspora (Europe, Amérique du Nord) |
| Virements | Comptes séquestres chez une banque partenaire ; import des relevés (fichiers ou API bancaire) |
| Espèces | Saisie au guichet avec reçu numéroté et double contrôle |
| Architecture | Module `Paiements` avec un adaptateur par fournisseur, clés d'idempotence, webhooks vérifiés, rapprochement automatique quotidien |
| Reversements | Virements groupés et paiements mobile money sortants, double validation obligatoire |

### 3.8 Communication
- E-mail transactionnel : Amazon SES, Brevo ou équivalent.
- SMS : agrégateur local (meilleure délivrabilité et coût au Cameroun) + Twilio en secours.
- **WhatsApp Business API** : rappels de loyer, confirmations de visite.
- **USSD** (V2) : consulter son solde et payer sans smartphone.
- Messagerie interne et notifications en temps réel : WebSocket (Socket.IO via NestJS).

### 3.9 Identité et sécurité
| Élément | Choix |
|---|---|
| Identité | **Keycloak** (OIDC) : comptes, rôles, MFA, SSO pour partenaires, connexion par SMS (code à usage unique) |
| Autorisations | Rôles + attributs (agence, portefeuille, lot) ; vérifiées dans le backend **et** par Row-Level Security en base |
| Secrets | HashiCorp Vault ou gestionnaire de secrets du cloud |
| Protection | WAF, limitation de débit, en-têtes de sécurité, analyse des dépendances (Dependabot, Trivy) |
| Anti-fraude | Double validation des virements, gel après changement de RIB, alertes d'anomalies |
| Données personnelles | Chiffrement des pièces sensibles, purge automatique des dossiers de candidats, registre des traitements |

### 3.10 Intelligence artificielle
| Usage | Approche |
|---|---|
| Lecture de documents (factures, CNI, avis d'imposition, titres) | API Claude (vision) avec sortie structurée, validation humaine des champs critiques |
| Rédaction d'annonces, courriers, comptes rendus | API Claude (modèle rapide et économique) |
| Assistant locataire et propriétaire 24 h/24 | API Claude avec accès en lecture aux données de l'utilisateur via des outils contrôlés, escalade vers un humain |
| Qualification des tickets à partir de photos | API Claude (vision) |
| Estimation de loyers et de prix, score de risque d'impayé | Modèles statistiques classiques (Python, scikit-learn) entraînés sur vos données, servis par un petit service séparé en V3 |
| Garde-fous | Aucune décision automatique sur la sélection d'un locataire ou une retenue ; journal de chaque suggestion |

### 3.11 Infrastructure et exploitation
| Élément | Choix |
|---|---|
| Conteneurs | Docker |
| Hébergement | Démarrage sur conteneurs gérés (Cloud Run, AWS ECS, Azure Container Apps ou Scaleway) ; **Kubernetes** seulement quand la charge le justifie |
| Région | Région cloud la plus proche (Afrique du Sud ou Europe) ou hébergeur local ; **vérifier les exigences de localisation des données** de la loi camerounaise sur les données personnelles |
| Infrastructure as code | **Terraform** |
| CI/CD | **GitHub Actions** : tests, analyse de sécurité, construction des images, déploiement par environnement (dev, recette, production) |
| Observabilité | OpenTelemetry → Grafana (Prometheus, Loki, Tempo) ; **Sentry** pour les erreurs web et mobile |
| Disponibilité | Base en haute disponibilité, au moins 2 instances backend, sauvegardes testées chaque mois |
| CDN | Cloudflare (cache, protection DDoS, images) |

### 3.12 Qualité et tests
- Tests unitaires : Jest (backend), Vitest ou Jest (front).
- Tests d'intégration sur une vraie base PostgreSQL (Testcontainers).
- **Tests de propriétés sur la comptabilité** : équilibre de chaque écriture, représentation des fonds, arrondis.
- Tests de bout en bout : **Playwright** (web) et Appium ou Detox (mobile) sur les parcours clés : paiement, reversement, signature du bail.
- Revue de code obligatoire, couverture minimale sur les modules financiers.

---

## 4. Organisation du code

```
plateforme/
├── apps/
│   ├── api/              # NestJS : API + workers
│   ├── web/              # Angular : back-office + espaces
│   ├── vitrine/          # Angular SSR : site public et annonces
│   └── mobile/           # Ionic/Capacitor : apps mobiles
├── libs/
│   ├── ui-quitus/        # Composants et jetons de la charte
│   ├── api-client/       # Client typé généré depuis OpenAPI
│   ├── domain/           # Types et règles partagés (montants, statuts)
│   └── i18n/
├── infra/                # Terraform, Docker, scripts
└── docs/
```
Monorepo géré avec **Nx** : constructions et tests incrémentaux, règles de dépendances entre modules.

Modules du backend (`apps/api/src/modules/`) : `patrimoine`, `tiers`, `mandats`, `location`, `saisonnier`, `vente`, `terrains`, `comptabilite`, `paiements`, `travaux`, `crm`, `documents`, `contentieux`, `assurances`, `fiscalite`, `reporting`, `notifications`, `administration`.

---

## 5. Montée en charge prévue

| Étape | Volume indicatif | Évolutions |
|---|---|---|
| MVP | < 5 000 lots | Un monolithe, une base, Redis, stockage objet |
| V1–V2 | 5 000 – 50 000 lots | Réplique en lecture, workers séparés de l'API, Meilisearch, CDN |
| V3 | > 50 000 lots, plusieurs pays | Extraction éventuelle des modules Paiements et Notifications en services, entrepôt de données, Kubernetes, bus d'événements (NATS ou Kafka) |

---

## 6. Équipe de démarrage recommandée

| Rôle | Nombre |
|---|---|
| Responsable technique / architecte | 1 |
| Développeurs full-stack TypeScript (Angular + NestJS) | 3 à 4 |
| Développeur mobile (Ionic) | 1 |
| Ingénieur DevOps (temps partiel au début) | 0,5 |
| Testeur / QA | 1 |
| Designer produit (charte Quitus) | 0,5 |
| Expert métier gestion immobilière + comptable | consultants |

---

## 7. Décisions à confirmer

1. **Langage du backend** : TypeScript/NestJS (recommandé) ou C#/.NET selon les compétences de l'équipe.
2. **Agrégateur de paiement** : un contrat unique ou des intégrations directes Orange Money et MTN MoMo.
3. **Hébergement** : cloud international ou hébergeur local, selon les exigences de localisation des données.
4. **Prestataire de signature électronique** : valeur juridique à valider pour chaque pays visé.
5. **Banque partenaire** pour les comptes séquestres et l'accès aux relevés.
