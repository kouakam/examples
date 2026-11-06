# Plateforme intégrée de gestion immobilière — Stack technique 100 % libre

> Complète `SPECIFICATIONS_FONCTIONNELLES.md` et les maquettes d'écran.
> Version 2.0 — novembre 2026
>
> **Exigence** : uniquement des logiciels libres et open source, auto-hébergeables, sans licence
> payante, sans abonnement et sans dépendance à un éditeur ou à un cloud particulier.

---

## 1. Règles de sélection

Chaque composant retenu doit :
1. être sous **licence libre reconnue** (MIT, Apache 2.0, BSD, MPL, GPL, AGPL, LGPL) ;
2. être **auto-hébergeable** sur vos propres serveurs ou chez n'importe quel hébergeur ;
3. être **remplaçable** : formats et protocoles ouverts (SQL, S3, OIDC, OpenAPI, SMTP, OpenTelemetry) ;
4. être **maintenu activement** par une communauté ou une fondation, pas par un seul éditeur susceptible de changer la licence.

Pour cette dernière raison, plusieurs outils connus sont **écartés** au profit de leur alternative communautaire :

| Outil écarté | Raison | Remplacé par |
|---|---|---|
| Redis | Licence modifiée en 2024 (licences non libres, puis AGPL ajoutée en 2025) : risque de nouveau changement | **Valkey** (BSD, Linux Foundation) |
| Terraform | Passé sous licence BSL (non libre) en 2023 | **OpenTofu** (MPL, Linux Foundation) |
| HashiCorp Vault | Passé sous licence BSL en 2023 | **OpenBao** (MPL, Linux Foundation) |
| Sentry | Licence FSL, non libre | **GlitchTip** (MIT, compatible avec les SDK Sentry) |
| MinIO | Édition communautaire réduite en 2025 (console retirée, distribution en sources seulement) | **SeaweedFS** (Apache 2.0) ou **Garage** (AGPL) |
| GitHub / GitHub Actions | Service propriétaire | **Forgejo** + Forgejo Actions ou **Woodpecker CI** |
| Cloudflare | Service propriétaire | Nginx/Traefik + cache + **imgproxy** |
| API d'IA commerciales | Paiement à l'usage | **Modèles ouverts** auto-hébergés (vLLM / Ollama) |
| Firebase, Stripe, WhatsApp Business, SES | Services propriétaires | Voir sections 3.3, 3.7 et 3.8 |

---

## 2. Vue d'ensemble

```
            ┌──────────────── Clients ─────────────────┐
            │ Web (Angular) · Apps mobiles (Ionic/      │
            │ Capacitor) · Site vitrine (Angular SSR)   │
            │ API partenaires · Webhooks · SMS          │
            └───────────────────┬──────────────────────┘
                                │ HTTPS (Let's Encrypt)
              ┌─────────────────▼──────────────────┐
              │ Traefik + Coraza WAF (règles OWASP)│
              │ + imgproxy (images)                 │
              └─────────────────┬──────────────────┘
                                │
   ┌────────────────────────────▼─────────────────────────────┐
   │ Backend NestJS (TypeScript) — monolithe modulaire         │
   │ API REST (OpenAPI) · Workers BullMQ · WebSocket           │
   └──┬──────────┬───────────┬──────────┬──────────┬──────────┘
      │          │           │          │          │
 PostgreSQL   Valkey     SeaweedFS  Meilisearch  Keycloak
 + PostGIS   (cache,    (stockage   (recherche)  (identité,
 (données,    files)     S3)                      MFA, SSO)
 grand livre)
      │
  Réplique → Apache Superset (BI)       Services annexes : Gotenberg (PDF),
                                        ClamAV, Tesseract, vLLM (IA),
                                        Jasmin (SMS), Postal (e-mail),
                                        Documenso (signature), ntfy (push)
```

---

## 3. Composants, couche par couche

### 3.1 Front web (back-office, espaces propriétaire, partenaire, prestataire)
| Élément | Choix | Licence |
|---|---|---|
| Framework | **Angular** (composants autonomes, signaux) — compatible avec la charte Quitus | MIT |
| Composants de base | Angular CDK + composants de la charte Quitus | MIT |
| État | Signaux Angular + NgRx Signal Store | MIT |
| Tableaux | **TanStack Table** (ou AG Grid Community, MIT) | MIT |
| Graphiques | **Apache ECharts** | Apache 2.0 |
| Cartes | **MapLibre GL JS** | BSD-3 |
| Fonds de carte | Tuiles **OpenStreetMap** auto-hébergées au format **PMTiles** (Protomaps) — un seul fichier servi par Nginx, aucun serveur de tuiles tiers | BSD / ODbL (données) |
| Géocodage d'adresses | **Nominatim** ou **Photon** auto-hébergé, données OSM du Cameroun | GPL / Apache 2.0 |
| Icônes | **Lucide** | ISC |
| Polices | Sora et Inter, hébergées sur vos serveurs | OFL |
| Internationalisation | Angular i18n | MIT |

### 3.2 Site vitrine et annonces
| Élément | Choix | Licence |
|---|---|---|
| Rendu serveur (référencement) | **Angular SSR** | MIT |
| Images | **imgproxy** (redimensionnement WebP/AVIF à la volée) + cache Nginx | MIT / BSD |
| Mesure d'audience | **Matomo** ou **Plausible CE** (respect de la vie privée) | GPL / AGPL |

### 3.3 Applications mobiles
| Élément | Choix | Licence |
|---|---|---|
| Framework | **Ionic + Capacitor** (Angular, même code que le web) | MIT |
| Base locale hors-ligne | **SQLite** (plugin Capacitor community) | Domaine public / MIT |
| Synchronisation | File d'opérations locale + API de synchronisation maison | — |
| Caméra, géolocalisation, fichiers | Plugins Capacitor officiels | MIT |
| Notifications | **ntfy** auto-hébergé + **UnifiedPush** sur Android ; repli par SMS | Apache 2.0 / GPL |
| Version installable sans magasin | **PWA** (service worker Angular) | MIT |

> **Limite à connaître** : sur iPhone, les notifications d'une application native passent obligatoirement par le service d'Apple (APNs, gratuit mais non libre). Sur Android, une application publiée sur Google Play utilise en pratique Firebase (gratuit). ntfy/UnifiedPush évitent Google pour les appareils qui l'acceptent. Les messages importants (loyer, urgence) partent aussi par SMS.

### 3.4 Backend
| Élément | Choix | Licence |
|---|---|---|
| Langage / exécution | **TypeScript** sur **Node.js** LTS | Apache 2.0 / MIT |
| Framework | **NestJS** (monolithe modulaire, un module par domaine métier) | MIT |
| ORM | **Drizzle ORM** ou **MikroORM** + SQL brut pour la comptabilité | Apache 2.0 / MIT |
| API | REST + **OpenAPI** (Swagger), webhooks signés | MIT |
| Validation | **Zod** (schémas partagés front/back) | MIT |
| Tâches de fond | **BullMQ** sur Valkey | MIT |
| Processus longs (vente, contentieux) | **Temporal** (auto-hébergé) — à partir de la V2 | MIT |
| Temps réel | **Socket.IO** | MIT |

> Alternative si l'équipe est C# : **.NET** (ASP.NET Core + EF Core), également sous licence MIT et entièrement libre.

### 3.5 Données
| Élément | Choix | Licence |
|---|---|---|
| Base principale | **PostgreSQL** | PostgreSQL (libre) |
| Géographie (parcelles, bornes, lotissements) | **PostGIS** | GPL |
| Haute disponibilité | **Patroni** + **etcd** (bascule automatique) | MIT / Apache 2.0 |
| Pool de connexions | **PgBouncer** | ISC |
| Cache et files | **Valkey** | BSD-3 |
| Recherche (annonces, lots, tiers) | **Meilisearch** (édition communautaire) ou **OpenSearch** | MIT / Apache 2.0 |
| Analytique (V3) | **ClickHouse** | Apache 2.0 |
| BI / tableaux de bord internes | **Apache Superset** (ou Metabase, AGPL) | Apache 2.0 |
| Sauvegardes PostgreSQL | **pgBackRest** (restauration à un instant donné) | MIT |
| Sauvegardes fichiers | **Restic** ou **BorgBackup**, copie chiffrée hors site | BSD / BSD |

Principes inchangés pour la comptabilité :
- Multi-locataire par `tenant_id` + **Row-Level Security** PostgreSQL.
- Grand livre en **ajout seul** (corrections par contre-passation), équilibre vérifié à chaque transaction.
- Montants en **entiers** (plus petite unité) + code devise. Jamais de nombres à virgule flottante.
- Journal d'audit en ajout seul, chaîné par empreinte (SHA-256).

### 3.6 Documents
| Élément | Choix | Licence |
|---|---|---|
| Stockage objet compatible S3 | **SeaweedFS** (ou **Garage**) | Apache 2.0 / AGPL |
| Antivirus des fichiers déposés | **ClamAV** | GPL |
| Génération PDF (baux, quittances, CRG) | Modèles **Handlebars** → **Gotenberg** | MIT / MIT |
| OCR | **Tesseract** ou **PaddleOCR** | Apache 2.0 |
| Signature électronique | **Documenso** ou **DocuSeal** (parcours multi-signataires) | AGPL |
| Signature PDF avancée (certificats, PAdES) | Bibliothèque **DSS** de la Commission européenne | LGPL |
| Horodatage | Serveur d'horodatage RFC 3161 (OpenSSL TSA / **Signserver CE**) | Apache 2.0 / LGPL |
| GED (option) | Module maison ; **Paperless-ngx** pour le classement interne | GPL |

> **Limite juridique** : un logiciel libre produit des signatures techniquement solides, mais une signature « qualifiée » au sens légal exige un certificat délivré par une autorité de certification reconnue dans le pays. À faire valider par un juriste pour le Cameroun et chaque pays visé.

### 3.7 Paiements
| Besoin | Choix | Licence |
|---|---|---|
| Mobile money | Intégration **directe** des API Orange Money et MTN MoMo, sans agrégateur intermédiaire | — |
| Orchestration (option, V2) | **Hyperswitch** (routage multi-fournisseurs, réessais, rapprochement) | Apache 2.0 |
| Virements | Comptes séquestres bancaires ; import des relevés (formats CSV, MT940, CAMT.053) avec un analyseur maison | — |
| Espèces | Saisie au guichet, reçu numéroté, double contrôle | — |
| Architecture | Module `Paiements` : un adaptateur par opérateur, clés d'idempotence, webhooks vérifiés, rapprochement quotidien | — |

> **Limite** : les opérateurs prélèvent des frais par transaction. Aucun logiciel ne peut les supprimer ; l'intégration directe évite seulement la commission d'un agrégateur.

### 3.8 Communication
| Canal | Choix | Licence |
|---|---|---|
| E-mail | **Postal** (serveur d'envoi complet) ou Postfix + OpenDKIM | MIT / IPL |
| SMS | **Jasmin SMS Gateway** connecté aux opérateurs en SMPP ; ou passerelle sur téléphones Android (application open source « SMS Gateway for Android ») pour démarrer | Apache 2.0 |
| Support client multicanal | **Chatwoot** (e-mail, chat du site, SMS, Telegram) | MIT |
| Messagerie instantanée | **Telegram Bot API** (gratuite) ; WhatsApp seulement en option, car payant par conversation | — |
| Notifications push | **ntfy** (voir 3.3) | Apache 2.0 |

> **Limite** : l'envoi de SMS et l'accès USSD passent par les opérateurs, qui facturent le volume. Le logiciel est libre, pas le réseau.

### 3.9 Identité et sécurité
| Élément | Choix | Licence |
|---|---|---|
| Identité, MFA, SSO, connexion par code SMS | **Keycloak** | Apache 2.0 |
| Secrets | **OpenBao** | MPL 2.0 |
| Proxy inverse et TLS | **Traefik** (ou Nginx / Caddy) + certificats **Let's Encrypt** gratuits | MIT / BSD / Apache 2.0 |
| WAF | **Coraza** + règles **OWASP CRS** | Apache 2.0 |
| Protection contre la force brute | **CrowdSec** ou Fail2ban | MIT / GPL |
| Analyse des vulnérabilités | **Trivy** (images, dépendances), **Semgrep CE** (code), **Renovate** (mises à jour) | Apache 2.0 / LGPL / AGPL |
| Tests d'intrusion | **OWASP ZAP** | Apache 2.0 |

### 3.10 Intelligence artificielle (auto-hébergée)
| Usage | Choix | Licence |
|---|---|---|
| Serveur de modèles | **vLLM** (production, GPU) ou **Ollama** (petits volumes) | Apache 2.0 / MIT |
| Modèles de langage | Modèles à poids ouverts sous **Apache 2.0** (familles Mistral, Qwen…) ; vérifier la licence de chaque modèle avant usage commercial | Apache 2.0 |
| Lecture de documents | OCR (Tesseract/PaddleOCR) + modèle vision-langage ouvert pour extraire les champs | Apache 2.0 |
| Recherche dans les documents (assistant) | **pgvector** dans PostgreSQL | PostgreSQL |
| Estimation de loyers, risque d'impayé | **scikit-learn** / **LightGBM** en Python | BSD / MIT |
| Garde-fous | Validation humaine des décisions sensibles, journal de chaque suggestion | — |

> **Limite** : un modèle ouvert est gratuit, mais il faut une machine avec carte graphique pour le faire tourner. Ce module est optionnel ; la plateforme fonctionne sans IA.

### 3.11 Infrastructure et exploitation
| Élément | Choix | Licence |
|---|---|---|
| Système | **Debian** ou **Ubuntu Server** | Libre |
| Virtualisation (serveurs physiques) | **Proxmox VE** | AGPL |
| Conteneurs | **Podman** ou **Docker Engine** (Moby) — pas Docker Desktop, payant pour les grandes entreprises | Apache 2.0 |
| Orchestration | **Docker Compose** au démarrage ; **k3s** (Kubernetes léger) ensuite | Apache 2.0 |
| Infrastructure as code | **OpenTofu** + **Ansible** | MPL 2.0 / GPL |
| Dépôt de code, revue, tickets | **Forgejo** (ou GitLab CE) | GPL / MIT |
| Intégration et déploiement continus | **Forgejo Actions** ou **Woodpecker CI** | GPL / Apache 2.0 |
| Registre d'images | **Harbor** (ou registre intégré à Forgejo) | Apache 2.0 |
| Métriques | **Prometheus** + **Grafana** | Apache 2.0 / AGPL |
| Journaux | **Loki** (ou OpenSearch) | AGPL |
| Traces | **OpenTelemetry** + **Tempo** (ou Jaeger) | Apache 2.0 / AGPL |
| Erreurs web et mobile | **GlitchTip** | MIT |
| Surveillance de disponibilité | **Uptime Kuma** | MIT |
| Hébergement | Vos serveurs, un datacenter local ou tout hébergeur de VPS : rien n'est lié à un fournisseur | — |

### 3.12 Qualité et tests
| Type | Outil | Licence |
|---|---|---|
| Unitaires | **Vitest** / **Jest** | MIT |
| Intégration (vraie base) | **Testcontainers** | MIT |
| Propriétés (comptabilité) | **fast-check** | MIT |
| Bout en bout web | **Playwright** | Apache 2.0 |
| Bout en bout mobile | **Appium** | Apache 2.0 |
| Charge | **k6** | AGPL |
| Monorepo | **Nx** (sans Nx Cloud) | MIT |

---

## 4. Ce qui ne peut pas être gratuit

Le logiciel est entièrement libre ; ces postes restent incompressibles :

| Poste | Ordre de grandeur |
|---|---|
| Serveurs (achat ou location), électricité, bande passante | selon volume |
| Frais par transaction mobile money et bancaires | fixés par les opérateurs |
| SMS et éventuel USSD | au volume, auprès des opérateurs |
| Publication des applications | Apple : abonnement annuel ; Google : frais unique |
| Nom de domaine | annuel |
| Certificat de signature qualifié (si exigé par la loi) | auprès d'une autorité de certification |
| Carte graphique pour l'IA (optionnel) | achat ou location |

---

## 5. Points de vigilance sur les licences

- **MIT, Apache, BSD, MPL** : aucune contrainte particulière pour un usage commercial.
- **AGPL** (Grafana, Loki, Tempo, Documenso, DocuSeal, Garage, Metabase, k6…) : libre d'utilisation. Si vous **modifiez** le code de ces logiciels et les proposez à des utilisateurs par le réseau, vous devez publier vos modifications. Les utiliser tels quels, à côté de votre propre code, ne vous oblige à rien sur votre code.
- **GPL** (PostGIS, ClamAV) : utilisés comme services séparés, ils n'imposent rien à votre code.
- Votre propre code reste votre propriété ; vous choisissez sa licence.
- Tenir un **inventaire des licences** (SBOM généré par Trivy) à chaque version.

---

## 6. Organisation du code

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
├── infra/                # OpenTofu, Ansible, Compose, manifests k3s
└── docs/
```
Modules du backend : `patrimoine`, `tiers`, `mandats`, `location`, `saisonnier`, `vente`, `terrains`, `comptabilite`, `paiements`, `travaux`, `crm`, `documents`, `contentieux`, `assurances`, `fiscalite`, `reporting`, `notifications`, `administration`.

---

## 7. Montée en charge

| Étape | Volume indicatif | Déploiement |
|---|---|---|
| MVP | < 5 000 lots | 3 serveurs : application, base de données, sauvegardes ; Docker Compose |
| V1–V2 | 5 000 – 50 000 lots | PostgreSQL en haute disponibilité (Patroni), workers séparés, Meilisearch, réplique pour la BI |
| V3 | > 50 000 lots, plusieurs pays | Cluster k3s, ClickHouse, extraction éventuelle des modules Paiements et Notifications, serveur GPU pour l'IA |

---

## 8. Équipe de démarrage

| Rôle | Nombre |
|---|---|
| Responsable technique / architecte | 1 |
| Développeurs full-stack TypeScript (Angular + NestJS) | 3 à 4 |
| Développeur mobile (Ionic) | 1 |
| Administrateur systèmes / DevOps (auto-hébergement) | 1 |
| Testeur / QA | 1 |
| Designer produit | 0,5 |
| Experts métier (gestion immobilière, comptabilité, juriste) | consultants |

> L'auto-hébergement complet demande un administrateur systèmes à temps plein dès le départ (mises à jour de sécurité, sauvegardes, supervision).

---

## 9. Décisions à confirmer

1. **Langage du backend** : TypeScript/NestJS (recommandé) ou C#/.NET, tous deux libres.
2. **Hébergement** : serveurs en propre, datacenter local ou VPS, selon les exigences de localisation des données de la loi camerounaise.
3. **Accès opérateurs** : contrats directs Orange et MTN pour le mobile money et l'envoi de SMS (SMPP).
4. **Signature électronique** : valeur juridique et autorité de certification à valider par pays.
5. **Module IA** : dès la V1 sur un serveur GPU, ou reporté à la V3.
