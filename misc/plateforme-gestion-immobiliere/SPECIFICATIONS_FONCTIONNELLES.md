# Plateforme intégrée de gestion immobilière — Spécifications fonctionnelles

> Document de référence métier : processus, modules et fonctionnalités d'une plateforme couvrant
> la **gestion locative**, la **transaction (vente de biens bâtis et de terrains)** et le
> **mandat de gestion de patrimoine** pour particuliers et partenaires.
>
> Version 1.0 — novembre 2026

---

## Sommaire

1. [Vision et périmètre](#1-vision-et-périmètre)
2. [Acteurs et rôles](#2-acteurs-et-rôles)
3. [Architecture fonctionnelle (vue d'ensemble des modules)](#3-architecture-fonctionnelle)
4. [Module 1 — Référentiel du patrimoine (biens, lots, terrains)](#4-module-1--référentiel-du-patrimoine)
5. [Module 2 — Mandats et onboarding des propriétaires](#5-module-2--mandats-et-onboarding-des-propriétaires)
6. [Module 3 — Gestion locative (cycle complet)](#6-module-3--gestion-locative)
7. [Module 4 — Location saisonnière / courte durée](#7-module-4--location-saisonnière--courte-durée)
8. [Module 5 — Transaction : vente de biens bâtis](#8-module-5--transaction--vente-de-biens-bâtis)
9. [Module 6 — Transaction : vente de terrains et lotissements](#9-module-6--transaction--vente-de-terrains-et-lotissements)
10. [Module 7 — Comptabilité mandant, trésorerie et paiements](#10-module-7--comptabilité-mandant-trésorerie-et-paiements)
11. [Module 8 — Maintenance, travaux et prestataires](#11-module-8--maintenance-travaux-et-prestataires)
12. [Module 9 — Copropriété / syndic (optionnel)](#12-module-9--copropriété--syndic-optionnel)
13. [Module 10 — CRM, marketing et diffusion](#13-module-10--crm-marketing-et-diffusion)
14. [Module 11 — Portails et applications (propriétaire, locataire, acquéreur, prestataire)](#14-module-11--portails-et-applications)
15. [Module 12 — GED, signature électronique et conformité](#15-module-12--ged-signature-électronique-et-conformité)
16. [Module 13 — Reporting, transparence et pilotage](#16-module-13--reporting-transparence-et-pilotage)
17. [Module 14 — Contentieux et recouvrement](#17-module-14--contentieux-et-recouvrement)
18. [Module 15 — Assurances et sinistres](#18-module-15--assurances-et-sinistres)
19. [Module 16 — Fiscalité et déclarations](#19-module-16--fiscalité-et-déclarations)
20. [Module 17 — Intelligence artificielle et automatisations](#20-module-17--intelligence-artificielle-et-automatisations)
21. [Module 18 — Administration, sécurité et paramétrage](#21-module-18--administration-sécurité-et-paramétrage)
22. [Intégrations externes](#22-intégrations-externes)
23. [Exigences non fonctionnelles](#23-exigences-non-fonctionnelles)
24. [Modèle de données (entités principales)](#24-modèle-de-données)
25. [Modèle économique de la plateforme](#25-modèle-économique)
26. [Feuille de route recommandée (MVP → V3)](#26-feuille-de-route)
27. [Indicateurs clés (KPI)](#27-indicateurs-clés-kpi)
28. [Annexes : statuts, workflows et checklists](#28-annexes)

---

## 1. Vision et périmètre

### 1.1 Vision
Offrir **un guichet unique** où un propriétaire (particulier, investisseur, institutionnel, promoteur,
partenaire apporteur) confie tout ou partie de son patrimoine, et suit **en temps réel**, avec une
**transparence totale**, chaque euro/franc encaissé ou dépensé, chaque document, chaque intervention,
chaque décision.

### 1.2 Principes directeurs
| Principe | Traduction concrète |
|---|---|
| **Transparence** | Accès 24/7 du mandant à ses comptes, pièces justificatives, devis, factures, photos, historique des échanges. Aucun frais non visible. |
| **Traçabilité** | Journal d'audit horodaté et inaltérable de toute action (qui, quoi, quand, avant/après). |
| **Séparation des fonds** | Fonds des mandants cantonnés sur compte séquestre / compte mandant, distincts des fonds de l'agence. |
| **Automatisation** | Quittancement, relances, révisions, régularisations, reversements générés automatiquement. |
| **Mobilité** | Applications mobiles pour tous les acteurs, état des lieux et visites sur tablette, mode hors-ligne. |
| **Conformité** | Respect de la réglementation locale (ex. France : loi Hoguet, ALUR, ELAN, RGPD, LCB-FT ; zone OHADA : droit foncier, titre foncier, AUDCG pour le bail commercial). |
| **Modularité** | Activation des modules par client (agence, gestionnaire, bailleur institutionnel, promoteur). |
| **Multi-** | Multi-agences, multi-pays, multi-devises, multi-langues, multi-sociétés (SCI, SARL, holdings). |

### 1.3 Périmètre métier
- **Gestion locative** : habitation (nue, meublée), colocation, étudiant, bail mobilité, commercial, professionnel, mixte, parkings/boxes, entrepôts, terrains nus loués (bail rural, emphytéotique, à construction), locations saisonnières.
- **Transaction** : vente de logements, locaux commerciaux, immeubles de rapport, fonds de commerce/droit au bail, **terrains** (nus, viabilisés, agricoles, lotissements), VEFA / programmes neufs.
- **Gestion de patrimoine** : mandat de gestion complet, gestion déléguée partielle, conseil en valorisation et arbitrage (vendre / conserver / rénover).
- **Optionnel** : syndic de copropriété, gestion d'actifs pour investisseurs (asset management), conciergerie.

---

## 2. Acteurs et rôles

### 2.1 Acteurs externes
| Acteur | Besoins principaux |
|---|---|
| **Propriétaire / mandant particulier** | Confier ses biens, percevoir ses loyers, suivre ses comptes, valider les travaux, recevoir les documents fiscaux. |
| **Partenaire / investisseur institutionnel** | Gestion de portefeuilles volumineux, reporting consolidé, API, exports comptables, SLA. |
| **Promoteur / lotisseur** | Commercialisation de programmes neufs et lotissements, grille de prix, réservation, appels de fonds. |
| **Apporteur d'affaires / prescripteur** | Apporter des mandats/clients, suivre ses commissions. |
| **Locataire** | Rechercher un bien, candidater, signer, payer, signaler un incident, obtenir quittances et attestations. |
| **Garant / caution** | Signer l'acte de cautionnement, être informé des impayés. |
| **Acquéreur / prospect** | Recherche, alertes, visites, offres, financement, suivi du dossier jusqu'à l'acte. |
| **Vendeur** | Estimation, mandat, suivi des visites et offres, compromis, acte. |
| **Prestataire / artisan** | Recevoir ordres de service, déposer devis/factures, photos, planning. |
| **Notaire / géomètre / avocat / huissier (commissaire de justice)** | Échange de pièces, rendez-vous de signature, procédures. |
| **Banque / courtier** | Dossiers de financement, attestations, déblocages. |
| **Assureur** | Polices PNO, GLI, MRH, DO ; déclarations de sinistres. |
| **Administration** | Cadastre, conservation foncière, impôts, urbanisme. |
| **Voyageur (saisonnier)** | Réservation, check-in, accès, caution, avis. |

### 2.2 Acteurs internes
| Rôle | Responsabilités |
|---|---|
| **Direction / Super-admin** | Paramétrage global, stratégie, tableaux de bord consolidés. |
| **Responsable d'agence** | Pilotage de l'agence, validation des engagements, objectifs. |
| **Gestionnaire locatif** | Portefeuille de lots : baux, quittancement, incidents, relations bailleurs/locataires. |
| **Assistant(e) de gestion** | Saisie, courriers, relances, planification. |
| **Chargé de location** | Commercialisation des biens à louer, visites, sélection des candidats, entrées. |
| **Négociateur / agent commercial transaction** | Prospection, estimations, mandats de vente, visites, offres. |
| **Comptable mandant** | Encaissements, rapprochements, reversements, CRG, régularisations, clôtures. |
| **Responsable technique** | Maintenance, travaux, prestataires, états des lieux techniques. |
| **Juriste / contentieux** | Impayés, procédures, litiges, conformité. |
| **Service client** | Hotline multicanale, tickets. |
| **Auditeur / contrôleur** | Lecture seule sur comptes et journaux (commissaire aux comptes, garant financier). |

### 2.3 Gestion des droits (RBAC + ABAC)
- Rôles paramétrables avec permissions fines (lecture / création / modification / validation / suppression / export) par module et par objet.
- Restrictions par **périmètre** : agence, portefeuille, mandant, immeuble, lot.
- **Seuils de délégation** : ex. un gestionnaire valide les travaux < 500 €, au-delà validation du responsable puis du propriétaire.
- **Double validation** (principe des 4 yeux) pour les virements, modifications d'IBAN/RIB, remises de dettes.
- Délégation temporaire (congés), comptes invités (notaire, expert), accès multi-propriétaires (indivision, SCI avec plusieurs associés, usufruit/nue-propriété).

---

## 3. Architecture fonctionnelle

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ CANAUX : Site vitrine · Portail propriétaire · Portail locataire · Espace      │
│ acquéreur · Espace prestataire · Apps mobiles · Back-office · API partenaires  │
├──────────────────────────────────────────────────────────────────────────────┤
│ CRM & Marketing │ Transaction bâti │ Transaction terrains │ Location longue    │
│ (leads, diffu-  │ (estimation,     │ (foncier, lotisse-   │ durée (candidature,│
│ sion, campagnes)│ mandat, offres,  │ ment, bornage,       │ bail, quittance-   │
│                 │ compromis, acte) │ réservation)         │ ment, EDL, sortie) │
├─────────────────┼──────────────────┼──────────────────────┼────────────────────┤
│ Location saison-│ Maintenance &    │ Copropriété/Syndic   │ Contentieux &      │
│ nière (channel  │ travaux          │ (option)             │ recouvrement       │
│ manager)        │                  │                      │                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ SOCLE : Référentiel patrimoine · Tiers · Mandats · Comptabilité mandant &      │
│ agence · Paiements · GED & e-signature · Workflows · Notifications · Reporting │
│ · IA · Audit · Sécurité · Paramétrage                                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Module 1 — Référentiel du patrimoine

### 4.1 Hiérarchie des objets
`Portefeuille → Ensemble / Résidence / Site → Immeuble / Bâtiment → Lot (appartement, maison, local, parking, cave, terrain, parcelle) → Annexes (équipements, compteurs, clés)`

### 4.2 Fiche bien (données)
- **Identification** : référence interne, adresse normalisée, géolocalisation GPS, quartier/zone, références cadastrales (section, parcelle), n° de **titre foncier** / livre foncier, n° de lot de copropriété et tantièmes.
- **Caractéristiques** : type, surface habitable / utile / loi Carrez / terrain, nombre de pièces, étage, ascenseur, exposition, année de construction, état, matériaux, chauffage, eau chaude, équipements, mobilier (inventaire pour meublé), stationnement.
- **Technique et réglementaire** : DPE / diagnostics (amiante, plomb, électricité, gaz, termites, ERP/risques, bruit, assainissement), dates de validité et alertes de renouvellement, permis de construire, certificat de conformité, servitudes, zonage PLU/plan d'urbanisme, autorisations de mise en location (permis de louer), décence et indécence énergétique (interdictions de louer selon la classe énergétique).
- **Juridique** : propriétaire(s) et quotes-parts, démembrement (usufruit/nue-propriété), régime (pleine propriété, copropriété, bail emphytéotique), hypothèques et charges, origine de propriété, statut fiscal (LMNP, nu, défiscalisation Pinel/Denormandie/Loc'Avantages, etc.).
- **Financier** : prix d'acquisition, frais, travaux capitalisés, valeur vénale estimée (historique), emprunts liés (échéancier), taxe foncière, charges de copropriété, assurance PNO, rentabilité brute/nette, cash-flow.
- **Médias** : photos HD, vidéos, visite virtuelle 360°, plans 2D/3D, drone (terrains), documents.
- **Compteurs** : eau, électricité, gaz — numéros (PDL/PCE), relevés historisés.
- **Clés et accès** : trousseaux, badges, boîtes à clés connectées, suivi des remises (qui détient quoi).
- **Équipements** : chaudière, VMC, climatisation, électroménager, avec date d'installation, garantie, contrat d'entretien, plan de maintenance préventive.

### 4.3 Fonctionnalités
- Création rapide par import (Excel/CSV, API), duplication de lots, création d'un immeuble avec N lots en masse.
- Carte interactive du patrimoine (filtres : statut, vacance, rendement, risques).
- **Statut du lot en temps réel** : vacant, en commercialisation, réservé, loué, en préavis, en travaux, en vente, vendu, indisponible.
- Historique complet : tous les baux, locataires, travaux, sinistres, valeurs.
- Carnet d'entretien numérique du logement / de l'immeuble.
- Calcul automatique des indicateurs : taux d'occupation physique et financier, rendement, loyer au m², écart au marché.
- Alertes : diagnostic expiré, fin de garantie, contrôle réglementaire (ascenseur, extincteurs, légionelle), échéance d'assurance.

---

## 5. Module 2 — Mandats et onboarding des propriétaires

### 5.1 Types de mandats gérés
| Mandat | Objet |
|---|---|
| **Mandat de gestion locative complète** | Recherche locataire + rédaction bail + quittancement + encaissement + charges + travaux courants + reversements + fiscalité. |
| **Mandat de location seule (mise en location)** | Recherche et installation du locataire uniquement. |
| **Mandat de gestion partielle / à la carte** | Ex. encaissement seul, technique seule, assistance déclarative. |
| **Mandat de gestion saisonnière** | Exploitation courte durée (annonces, réservations, ménage, accueil). |
| **Mandat de vente simple / exclusif / semi-exclusif** | Commercialisation d'un bien ou terrain. |
| **Mandat de recherche (acquéreur)** | Recherche d'un bien pour un client acquéreur. |
| **Mandat de gestion de patrimoine global / asset management** | Portefeuille complet, arbitrages, plan pluriannuel. |
| **Convention partenaire / apporteur** | Rétrocession de commissions, règles de reporting. |

### 5.2 Processus d'onboarding du mandant
1. **Captation** : formulaire web « Confier mon bien », simulateur de revenus nets, prise de RDV, ou import partenaire via API.
2. **Qualification** : appel, collecte des besoins (type de gestion, objectifs, horizon).
3. **Estimation locative et/ou vénale** (voir 8.2) avec rapport PDF.
4. **Proposition commerciale** : grille d'honoraires, options (GLI, PNO, état des lieux, déclaration fiscale), simulation de revenu net.
5. **KYC / LCB-FT** : identité, justificatif de domicile, titre de propriété, Kbis/statuts pour personne morale, bénéficiaires effectifs, contrôle des listes de sanctions/PPE, origine des fonds pour transactions.
6. **Collecte des documents du bien** (checklist dynamique selon le type de bien).
7. **Signature électronique du mandat** (avec registre des mandats numéroté, chronologique et inaltérable).
8. **Paramétrage** : RIB de reversement (vérification de titularité), périodicité de reversement, seuils de validation travaux, préférences de communication, mandataires secondaires (co-indivisaires).
9. **Reprise de l'existant** si bien déjà loué : reprise du bail, dépôt de garantie transféré, solde locataire, historique.
10. **Activation de l'espace propriétaire** et message de bienvenue avec calendrier de gestion.

### 5.3 Gestion du cycle de vie du mandat
- Échéances, tacite reconduction, avenants (ajout/retrait de lots, changement d'honoraires), résiliation avec préavis, transfert de gestion vers/depuis un autre gestionnaire (dossier de passation automatique).
- Registre légal des mandats (numérotation, conservation).
- Suivi des obligations de reddition de comptes.
- Historique des engagements et consentements.

### 5.4 Grille d'honoraires paramétrable
- % des encaissements (HT/TTC), forfaits par lot, honoraires de location (parts bailleur/locataire avec plafonds réglementaires), honoraires d'état des lieux, frais de suivi de travaux (% du montant), frais de contentieux, honoraires de vente (% ou forfait, à la charge vendeur ou acquéreur), dégressivité par volume pour les partenaires, minimums de facturation.

---

## 6. Module 3 — Gestion locative

### 6.1 Cycle de vie complet

```
Mise en location → Commercialisation → Candidatures → Sélection & solvabilité → Bail & garanties
→ État des lieux d'entrée → Vie du bail (quittancement, encaissement, charges, révisions, incidents,
travaux, assurances, renouvellement) → Congé → État des lieux de sortie → Restitution du dépôt
→ Remise en location
```

### 6.2 Préparation et commercialisation
- Détermination du loyer : comparables de marché, encadrement des loyers (loyer de référence majoré, complément de loyer justifié), historique du lot.
- Check pré-location : décence, DPE autorisé à la location, diagnostics valides, assurance PNO active, travaux de remise en état terminés.
- Génération automatique de l'annonce (texte assisté par IA, mentions légales obligatoires : loyer, charges, dépôt, honoraires, DPE/GES, surface).
- Multidiffusion vers portails, réseaux sociaux, site vitrine.
- Agenda de visites : créneaux en ligne, visites groupées, visites virtuelles, visites autonomes avec boîte à clés connectée et code temporaire.
- Feedback après visite et statistiques par annonce (vues, contacts, visites, taux de transformation).

### 6.3 Candidatures et sélection
- **Dossier locataire numérique** : formulaire, pièces justificatives (dans le respect de la liste légale des pièces autorisées), dossier certifié (type DossierFacile) ou import.
- **Contrôle anti-fraude documentaire** : détection de faux bulletins de salaire, avis d'imposition (vérification 2D-Doc / API fiscale), cohérence des données.
- **Scoring de solvabilité** : taux d'effort, stabilité des revenus, garanties ; règles paramétrables par propriétaire.
- **Garanties** : caution personne physique, garantie Visale, GLI (éligibilité automatique), caution bancaire, garant professionnel.
- Comparateur de candidats présenté au propriétaire, décision motivée et traçable, **non-discrimination** (critères verrouillés).
- Réponses automatiques aux candidats non retenus.

### 6.4 Contractualisation
- Bibliothèque de **modèles de baux** : vide, meublé, colocation (bail unique / baux individuels), étudiant, mobilité, commercial (3/6/9), professionnel, mixte, parking, saisonnier, bail rural/emphytéotique pour terrains, avenants.
- Génération automatique à partir des données du lot et du locataire, clauses optionnelles (solidarité, animaux, travaux, clause résolutoire), annexes obligatoires (notice d'information, diagnostics, règlement de copropriété, inventaire du mobilier).
- Acte de cautionnement avec mentions obligatoires.
- **Signature électronique** multipartite (bailleur ou mandataire, locataires, garants) avec ordre de signature.
- Encaissement en ligne du premier loyer, du dépôt de garantie et des honoraires avant remise des clés.
- Attestation d'assurance habitation obligatoire (collecte + relance annuelle + possibilité d'assurance pour compte du bailleur).
- Ouverture automatique des contrats énergies (lien fournisseurs) — optionnel.

### 6.5 États des lieux (EDL)
- Application mobile/tablette **hors-ligne**, pièce par pièce, élément par élément, état (neuf / bon / usage / dégradé), photos horodatées et géolocalisées, vidéos, relevés de compteurs, remise des clés.
- Modèles par type de bien ; reprise automatique de l'EDL d'entrée lors de la sortie pour **comparaison côte à côte**.
- Signature sur place par toutes les parties, envoi PDF immédiat.
- Délai de signalement de défauts après l'entrée (complément d'EDL par le locataire depuis son portail).
- Calcul des retenues avec **grille de vétusté** paramétrable (durée de vie, abattement annuel) et chiffrage par devis/barème.
- Inventaire du mobilier pour meublé.
- Prestation EDL externalisable (huissier / expert) avec intégration du PDF.

### 6.6 Quittancement et encaissement
- **Appels de loyers** automatiques (mensuel, trimestriel, terme à échoir/échu), loyer + provisions sur charges + taxes (ordures ménagères), TVA pour baux commerciaux optés.
- Prorata d'entrée/sortie automatique.
- Envoi multicanal (e-mail, portail, SMS, courrier).
- **Moyens de paiement** : prélèvement SEPA (mandats électroniques), virement avec IBAN virtuel dédié par locataire (rapprochement automatique), carte bancaire, **mobile money** (Orange Money, MTN MoMo, Wave, M-Pesa…), espèces au guichet avec reçu, chèque (remise numérisée), paiement des aides au logement en tiers payant (CAF/équivalent).
- Lettrage automatique et rapprochement bancaire.
- **Quittances** générées uniquement à paiement intégral, reçus pour paiements partiels.
- Avis d'échéance, attestations de loyer à jour, historiques de paiement.
- Gestion des échéanciers / plans d'apurement.

### 6.7 Charges et régularisations
- Provisions sur charges et forfaits de charges (selon type de bail).
- Imputation des charges récupérables (liste réglementaire) vs non récupérables.
- Import des budgets/décomptes du syndic ; répartition par tantièmes, compteurs, surface, personnes.
- **Régularisation annuelle** : décompte détaillé par nature, justificatifs consultables (droit de consultation), envoi automatique, solde au crédit/débit, ajustement des provisions.
- Refacturation de la taxe d'enlèvement des ordures ménagères.
- Relevés de compteurs individuels (télérelève, saisie locataire avec photo).

### 6.8 Révision, indexation, renouvellement
- Révision annuelle automatique selon l'indice (IRL, ILC, ILAT, ICC ou indice local/contractuel), date de référence, clause d'échelle mobile ; respect des gels/plafonnements réglementaires et de l'interdiction de révision pour logements énergivores le cas échéant.
- Courrier de révision automatique, historique des loyers.
- Rattrapage (dans la limite légale) et alerte si révision oubliée.
- **Renouvellement** : alertes d'échéance (bail commercial, bail meublé, bail mobilité non renouvelable), proposition de nouveau loyer (réévaluation si sous-évalué selon procédure), avenant ou nouveau bail.
- Baux commerciaux : plafonnement, déplafonnement, état des lieux des charges et travaux triennal, droit de préférence, renouvellement/congé par acte extrajudiciaire.

### 6.9 Vie du bail — relation locataire
- **Ticketing des demandes** (incident, question, attestation, changement de situation) avec catégorie, urgence, photos, vidéo, suivi en temps réel, SLA.
- Attribution automatique de la responsabilité (locataire / bailleur / copropriété) selon la nature (réparations locatives vs grosses réparations).
- Changements : ajout/retrait de colocataire, changement de garant, cession de bail, sous-location (autorisation), modification de RIB.
- Communications de masse par immeuble (coupure d'eau, travaux).
- Enquêtes de satisfaction.

### 6.10 Sortie du locataire
1. Réception du congé (formulaire en ligne, LRAR, acte) → calcul automatique du préavis (1 ou 3 mois, zones tendues, motifs de préavis réduit, meublé).
2. Congé délivré par le bailleur (vente, reprise, motif légitime et sérieux) : vérification des délais et mentions, droit de préemption du locataire en cas de vente, notification par commissaire de justice.
3. Relance commerciale immédiate du lot (annonce, visites pendant le préavis).
4. Planification de l'EDL de sortie.
5. Relevés de compteurs, restitution des clés.
6. Calcul du **solde de tout compte** : dernier loyer au prorata, régularisation des charges (retenue provisoire possible en copropriété), réparations locatives, impayés.
7. **Restitution du dépôt de garantie** dans les délais légaux (ex. 1 mois si EDL conforme, 2 mois sinon) avec calcul automatique des pénalités de retard, justificatifs des retenues.
8. Archivage du dossier et attestation de fin de bail.

### 6.11 Colocation, résidences gérées et cas particuliers
- Bail unique solidaire ou baux individuels par chambre, gestion des entrées/sorties partielles, quote-part de loyer et de dépôt.
- Résidences étudiantes/seniors/coliving : services, forfaits, gestion par chambre.
- Logement de fonction, logements sociaux/conventionnés (plafonds de ressources et de loyers).
- Location de terrains : baux agricoles, emphytéotiques, à construction, occupations temporaires, location de parcelles pour panneaux, antennes, stockage.

---

## 7. Module 4 — Location saisonnière / courte durée

- **Channel manager** : synchronisation des calendriers et des tarifs avec les plateformes de réservation (iCal/API), anti-surréservation.
- Moteur de réservation direct sur le site (paiement, caution par préautorisation).
- **Tarification dynamique** : saisonnalité, événements, durée minimale, remises longue durée, last-minute.
- Conformité : numéro d'enregistrement, déclaration en mairie, plafond de nuitées pour résidence principale, collecte et reversement de la **taxe de séjour**, fiche de police pour voyageurs étrangers lorsque requise.
- Messagerie voyageur automatisée (confirmation, instructions d'arrivée, livret d'accueil digital, avis).
- Check-in/out : remise de clés, boîte à clés ou serrure connectée avec codes temporaires, vérification d'identité.
- **Opérations** : planning ménage/blanchisserie généré par les réservations, check-lists photo, gestion du linge et consommables, inspection qualité.
- Gestion des dommages et de la caution, réclamations aux plateformes.
- Relevé de gestion propriétaire : nuitées, taux d'occupation, RevPAR, ADR, commissions plateformes, frais de ménage, revenu net.
- Bascule saisonnier ↔ bail mobilité ↔ longue durée selon la saison.

---

## 8. Module 5 — Transaction : vente de biens bâtis

### 8.1 Processus de vente de bout en bout
```
Prospection → Estimation → Mandat de vente → Préparation (diagnostics, photos, dossier) →
Diffusion → Gestion des acquéreurs & visites → Offres & négociation → Acceptation →
Avant-contrat (promesse/compromis) → Conditions suspensives (financement, urbanisme, préemption) →
Acte authentique → Facturation des honoraires → Après-vente (proposition de gestion locative)
```

### 8.2 Prospection et estimation
- Prospection géolocalisée (pige des annonces de particuliers, alertes de mise en vente, fichiers propriétaires, successions/DPE défavorables sous réserve de licéité).
- **Outil d'estimation** : comparables vendus (bases de transactions publiques type DVF ou équivalent local), annonces actives, méthode par capitalisation des loyers pour biens de rapport, ajustements qualitatifs, fourchette et indice de confiance.
- Avis de valeur PDF personnalisé et suivi de l'évolution.

### 8.3 Mandat de vente
- Mandat simple / exclusif / semi-exclusif, durée, prix, honoraires et qui les supporte, clause pénale, droit de rétractation (vente hors établissement / à distance), registre des mandats.
- Suivi des actions commerciales obligatoires (compte rendu périodique au vendeur pour l'exclusif).
- Gestion des baisses de prix (avenants) et de l'**inter-cabinet / fichier partagé** (partage d'honoraires).

### 8.4 Préparation du bien
- Checklist du dossier de vente : titre de propriété, diagnostics techniques, documents de copropriété (PV d'AG sur 3 ans, carnet d'entretien, fiche synthétique, pré-état daté, règlement), taxe foncière, permis/conformités, factures de travaux, garanties décennales.
- Home staging virtuel, photos professionnelles, visite 3D, plans.
- Data room vendeur partageable avec le notaire.

### 8.5 Gestion des acquéreurs
- Fiche acquéreur : critères (multi-critères, polygones de recherche sur carte), budget, capacité de financement (simulation, attestation courtier), situation (primo-accédant, investisseur), délai.
- **Rapprochement automatique** biens ↔ acquéreurs, alertes push/e-mail.
- Bons de visite signés électroniquement, comptes rendus de visite partagés avec le vendeur.
- Pré-qualification financière avant visite (score de sérieux).

### 8.6 Offres et négociation
- Offres d'achat en ligne signées, conditions (prix, financement, délai), contre-offres, historique, comparateur d'offres pour le vendeur.
- Gestion des **enchères/ventes interactives** (offres en temps réel, prix de réserve) — option.
- Acceptation → génération du dossier de transaction.

### 8.7 Avant-contrat et suivi jusqu'à l'acte
- Préparation du compromis/promesse (ou transmission au notaire), conditions suspensives, dépôt de garantie/indemnité d'immobilisation en séquestre.
- Délai de rétractation de l'acquéreur, notifications légales.
- **Rétroplanning** automatique : purge du droit de préemption (DIA), obtention du prêt, levée des conditions, état daté syndic, signature de l'acte.
- Portail partagé vendeur–acquéreur–notaire–courtier avec jalons et pièces.
- Facturation des honoraires à l'acte, partage inter-agences, commissions des négociateurs (barèmes, paliers).

### 8.8 Programmes neufs / VEFA
- Grille de lots (plan masse interactif), statut des lots en temps réel (disponible, optionné, réservé, vendu), options à durée limitée.
- Contrat de réservation, dépôt de garantie, appels de fonds selon l'avancement (échéancier légal), choix de prestations/TMA (travaux modificatifs), livraison avec réserves et levée des réserves, garanties (parfait achèvement, biennale, décennale).
- Reporting promoteur : rythme d'écoulement, CA réservé/acté, stocks.

### 8.9 Ventes spécifiques
- Immeuble de rapport et vente en bloc (rendement, état locatif, data room).
- Vente occupée (bail en cours transmis, notification au locataire).
- Viager (occupé/libre, bouquet, rente, calcul actuariel).
- Fonds de commerce, droit au bail, cession de parts de SCI.
- Vente à la découpe (droits de préemption des locataires).

---

## 9. Module 6 — Transaction : vente de terrains et lotissements

### 9.1 Spécificités foncières
- **Fiche terrain** : superficie (titrée vs mesurée), références cadastrales, **titre foncier / statut juridique** (titré, en cours d'immatriculation, droit coutumier, concession provisoire/définitive, bail emphytéotique), situation (plan de localisation), accès/voirie, viabilisation (eau, électricité, assainissement, télécoms), topographie, nature du sol, zonage d'urbanisme (constructible, agricole, naturel), coefficient d'emprise et hauteurs autorisées, servitudes, risques (inondation, glissement), présence d'occupants.
- **Due diligence foncière** (checklist et suivi) : authenticité du titre (vérification auprès de la conservation foncière), état des inscriptions (hypothèques, litiges, oppositions), certificat d'urbanisme, plan de bornage contradictoire par géomètre agréé, absence de double vente, situation fiscale, autorisations (lotir, morceler).
- Cartographie SIG : affichage des parcelles, superposition avec cadastre/zonage, photos drone, coordonnées des bornes.

### 9.2 Lotissements
- Création d'un lotissement : plan de masse, découpage en parcelles (surface, prix au m², position, statut), voiries et réseaux, cahier des charges, règlement de lotissement.
- Vente sur plan interactif : sélection de parcelle, option, réservation en ligne.
- **Vente à tempérament / paiement échelonné** : échéancier, acompte, pénalités, transfert de propriété à solde, relances automatiques, déchéance.
- Suivi des travaux de viabilisation et des autorisations (permis d'aménager).
- Morcellement et mutation des titres individuels ; délivrance des actes.
- Association syndicale / gestion des parties communes du lotissement.

### 9.3 Processus de vente d'un terrain
1. Mandat (propriétaire, indivision familiale, collectivité, promoteur) + vérification de la capacité à vendre (tous les ayants droit, mandat collectif).
2. Due diligence et constitution du dossier foncier.
3. Bornage / mise à jour du plan.
4. Mise en marché (annonce, carte, visite de terrain avec coordonnées GPS).
5. Offres, réservation, protocole d'accord.
6. Paiement (séquestre chez notaire ou compte séquestre de la plateforme).
7. Acte notarié, enregistrement, mutation au livre foncier.
8. Remise du titre/acte à l'acquéreur, archivage.
9. Option : accompagnement à la construction (architecte, permis, entreprise) et mise en gestion future.

### 9.4 Prévention des fraudes foncières
- Vérification croisée des titres, historique des transactions sur la parcelle dans la plateforme, alerte de double mise en vente, identité vérifiée des vendeurs, paiement exclusivement sur compte séquestre, aucune remise de fonds en espèces non tracée.

---

## 10. Module 7 — Comptabilité mandant, trésorerie et paiements

### 10.1 Principes
- **Comptabilité à double niveau** : comptabilité des mandants (fonds de tiers) + comptabilité de l'agence (honoraires). Partie double, plan comptable paramétrable (PCG, SYSCOHADA…).
- Comptes séquestres/mandants distincts, garantie financière, **représentation des fonds** à tout instant (le total dû aux mandants = solde des comptes mandants).
- Comptes individuels : un compte par mandant, par locataire, par lot, par fournisseur.

### 10.2 Fonctionnalités
- Encaissements multi-canaux, **rapprochement bancaire automatique** (flux bancaires, EBICS, open banking, relevés mobile money).
- Lettrage automatique / assisté par IA des paiements non identifiés.
- **Paiement des fournisseurs** pour compte du mandant (factures de travaux, syndic, assurances, taxes) avec workflow de validation et justificatifs attachés.
- **Reversements aux propriétaires** : périodicité (mensuelle, trimestrielle, à la demande), date fixe ou à encaissement, retenue d'une provision pour travaux / réserve de trésorerie, virements en masse (SEPA XML), multi-devises.
- Ventilation automatique des honoraires agence à chaque encaissement et facturation des honoraires.
- Gestion du **dépôt de garantie** (conservé par l'agence ou reversé au propriétaire selon mandat).
- Gestion de la TVA (baux commerciaux, meublés para-hôteliers), retenues à la source le cas échéant (non-résidents, fiscalité locale).
- **Compte rendu de gestion (CRG)** : relevé détaillé par période, par lot (loyers appelés, encaissés, impayés, charges payées, honoraires, reversements), avec liens vers chaque justificatif.
- Clôtures mensuelles et annuelles, balance, grand livre, journaux, FEC/export comptable, interface vers logiciels comptables.
- Contrôles automatiques : soldes anormaux, comptes débiteurs propriétaires, doublons de paiement, modification de RIB récente avant virement (anti-fraude au président/faux RIB).
- Gestion des emprunts du propriétaire (échéancier, ventilation intérêts/capital, intégration au cash-flow).
- Prévisionnel de trésorerie par mandant.

---

## 11. Module 8 — Maintenance, travaux et prestataires

### 11.1 Maintenance corrective
1. Signalement (locataire, gestionnaire, capteur IoT, visite).
2. Qualification (catégorie, urgence, responsabilité, garantie applicable) — assistée par IA à partir des photos/description.
3. Diagnostic à distance (tutoriels, auto-dépannage) ou intervention.
4. Sélection du prestataire (référencé, zone, spécialité, note, disponibilité, contrat cadre).
5. Devis (1 à 3 selon seuil) → validation selon délégation (gestionnaire / propriétaire via app en un clic).
6. **Ordre de service** avec créneau convenu avec le locataire.
7. Intervention : check-in géolocalisé, photos avant/après, rapport, signature du locataire.
8. Facture → contrôle (conformité au devis) → paiement pour compte → imputation (propriétaire / locataire / copro / assurance).
9. Clôture et évaluation de satisfaction.

### 11.2 Maintenance préventive et réglementaire
- Plans de maintenance par équipement (chaudière annuelle, ramonage, VMC, ascenseur, extincteurs, désinfection, entretien espaces verts), contrats d'entretien, génération automatique des interventions et relances.
- Suivi des contrôles obligatoires et des certificats.

### 11.3 Gros travaux et rénovation
- Gestion de projet : programme, budget, appels d'offres, comparatif de devis, planning (Gantt), suivi de chantier (photos, PV), réception avec réserves, levée des réserves, garanties.
- **Rénovation énergétique** : audit, scénarios de travaux, gains de classe énergétique, aides mobilisables, impact sur le loyer et la valeur.
- Plan pluriannuel de travaux par immeuble / portefeuille.

### 11.4 Référentiel prestataires
- Onboarding : documents légaux (immatriculation, assurances RC/décennale, attestations de vigilance), vérification périodique et alertes d'expiration.
- Évaluation (délais, qualité, prix), contrats cadres et bordereaux de prix, zones d'intervention.
- Portail prestataire : ordres de service, planning, devis, factures, photos, statut de paiement.

---

## 12. Module 9 — Copropriété / syndic (optionnel)

- Fiche copropriété : règlement, état descriptif de division, tantièmes et clés de répartition, conseil syndical.
- Budget prévisionnel, appels de fonds trimestriels, fonds de travaux, comptes copropriétaires.
- Assemblées générales : convocation, vote par correspondance et **AG en visio/hybride**, feuille de présence, calcul automatique des majorités, PV, notification.
- Gestion des contrats de l'immeuble, sinistres, carnet d'entretien, extranet copropriétaires.
- État daté, pré-état daté pour les ventes, immatriculation au registre des copropriétés.
- Interface avec le module gestion locative pour la récupération des charges.

---

## 13. Module 10 — CRM, marketing et diffusion

- **CRM unifié des tiers** : un contact peut être à la fois propriétaire, locataire, acquéreur, vendeur ; historique 360° (échanges, documents, transactions, tickets).
- Capture des leads : site, portails, réseaux sociaux, téléphonie (call tracking), chat, WhatsApp, formulaires partenaires.
- Pipeline commercial (Kanban) par type d'affaire : mandats de gestion, mandats de vente, acquéreurs, locations ; probabilités et prévisions de CA.
- Attribution automatique des leads (zone, charge, compétence), délai de premier contact suivi.
- Campagnes e-mail/SMS/WhatsApp, newsletters, séquences de nurturing, segmentation.
- **Multidiffusion** des annonces (portails nationaux et locaux, site, réseaux sociaux), suivi des performances par canal et coût par lead.
- **Site vitrine** intégré (CMS) avec moteur de recherche, carte, alertes, SEO, pages agences, avis clients.
- Programme apporteurs d'affaires et parrainage (suivi des commissions).
- Gestion des avis et de la réputation.
- Agenda partagé, synchronisation calendriers, tâches et rappels.

---

## 14. Module 11 — Portails et applications

### 14.1 Espace propriétaire (web + mobile) — cœur de la transparence
- **Tableau de bord** : revenus du mois, encaissé vs appelé, impayés, taux d'occupation, rendement, prochains événements.
- Liste des biens et statut en temps réel ; fiche détaillée de chaque bien.
- **Comptes en temps réel** : chaque mouvement avec sa pièce justificative (facture, devis, quittance), CRG téléchargeables, historique des reversements.
- **Validation en un clic** des devis, choix d'un candidat locataire, acceptation d'une offre d'achat, signature des avenants.
- Suivi des interventions avec photos avant/après.
- Coffre-fort documentaire (baux, EDL, diagnostics, attestations, actes, documents fiscaux).
- Messagerie avec le gestionnaire (traçée, SLA de réponse).
- Simulations : revalorisation de loyer, rénovation, vente vs conservation, projection fiscale.
- Valeur estimée du patrimoine et évolution.
- Pour partenaires/institutionnels : multi-portefeuilles, consolidation, exports, API, accès multi-utilisateurs.

### 14.2 Espace locataire
- Paiement en ligne, échéancier, historique, quittances et attestations téléchargeables.
- Déclaration d'incident avec photos/vidéo et suivi.
- Documents du bail, EDL, règlement intérieur, informations de l'immeuble.
- Dépôt de l'attestation d'assurance annuelle, relevés de compteurs.
- Congé en ligne, prise de RDV EDL de sortie.
- Messagerie, notifications, FAQ et assistant virtuel.

### 14.3 Espace candidat / acquéreur
- Recherche, favoris, alertes, prise de rendez-vous de visite, dossier de candidature, offres d'achat, suivi du dossier de vente avec jalons, simulateur de financement et de frais de notaire.

### 14.4 Espace prestataire
- Ordres de service, planning, devis/factures, photos, paiements, documents de conformité.

### 14.5 Applications collaborateurs
- App terrain : visites, EDL hors ligne, photos, signature, prise de mandat, scan de documents, dictée de comptes rendus, géolocalisation des biens.

---

## 15. Module 12 — GED, signature électronique et conformité

### 15.1 GED
- Classement automatique (OCR + IA : reconnaissance du type de document, extraction de données), rattachement au bon objet (bien, bail, tiers, transaction).
- Versioning, métadonnées, recherche plein texte, durées de conservation légales et purge automatique.
- Partage sécurisé (liens temporaires, data room), filigranes.
- Archivage à valeur probante (horodatage, coffre-fort numérique).

### 15.2 Signature électronique
- Signature simple/avancée/qualifiée selon l'acte, parcours multi-signataires, ordre de signature, relances, dossier de preuve.
- Lettre recommandée électronique pour les notifications légales (congés, révisions, mises en demeure) lorsque légalement admise.

### 15.3 Conformité réglementaire
- **Carte professionnelle** et habilitations des collaborateurs, attestations des agents commerciaux.
- Registres : mandats, répertoire des transactions, registre des réclamations.
- **LCB-FT** : KYC, évaluation des risques, déclaration de soupçon (circuit confidentiel), contrôle des espèces, conservation.
- **RGPD / protection des données** : registre des traitements, consentements, droits des personnes (accès, rectification, effacement, portabilité), minimisation des données des candidats, durée de conservation, analyse d'impact.
- Mentions obligatoires dans les annonces, affichage des honoraires.
- Veille réglementaire intégrée : mise à jour des modèles, indices, plafonds.

---

## 16. Module 13 — Reporting, transparence et pilotage

### 16.1 Reporting propriétaire
- CRG mensuel/trimestriel, relevé annuel, synthèse fiscale, rapport de performance (rendement, vacance, coûts), rapport d'activité (visites, interventions).
- Rapports personnalisables et planifiables, export PDF/Excel.

### 16.2 Pilotage interne
- Tableaux de bord par agence/gestionnaire/négociateur : nombre de lots, CA honoraires, taux d'impayés, vacance, délai de relocation, délai de traitement des tickets, productivité, mandats signés, ventes conclues, pipeline.
- Analyse du portefeuille : concentration des risques, échéances de baux, lots énergivores, potentiel de revalorisation.
- Alertes et rapports d'exception.
- Data warehouse et connecteur BI.

### 16.3 Transparence avancée
- **Journal d'activité visible par le propriétaire** (« fil d'actualité » de son bien).
- Comparaison avec le marché (loyer, charges, frais de gestion).
- Indicateurs de qualité de service publiés (SLA respectés, délais de reversement).

---

## 17. Module 14 — Contentieux et recouvrement

### 17.1 Recouvrement amiable (automatisé)
| J | Action |
|---|---|
| J+1 à J+5 | Relance douce automatique (SMS, e-mail, notification) avec lien de paiement |
| J+10 | Relance n°2 + appel du gestionnaire, proposition d'échéancier |
| J+15 | Mise en demeure (lettre recommandée) + information du garant |
| J+30 | Déclaration GLI / Visale dans les délais contractuels |
| J+30/45 | Commandement de payer par commissaire de justice (déclenchement clause résolutoire) |
| … | Procédure judiciaire |

- Scénarios paramétrables par propriétaire et par profil de risque ; détection précoce (score de risque d'impayé).
- Plans d'apurement signés électroniquement, suivi du respect.
- Accompagnement social (orientation vers aides, fonds de solidarité).

### 17.2 Contentieux judiciaire
- Dossier contentieux : pièces, chronologie, intervenants (avocat, commissaire de justice), frais, audiences, décisions, délais.
- Procédures : résiliation de bail, expulsion (avec respect des trêves et délais), recouvrement de créances, injonction de payer, litiges de dépôt de garantie, troubles de voisinage, litiges travaux, litiges de vente.
- Provisionnement comptable et passage en perte (créances irrécouvrables), refacturation des frais.
- Suivi des recours contre les assurances.

---

## 18. Module 15 — Assurances et sinistres

- Référentiel des polices : PNO, GLI, MRH des locataires, multirisque immeuble, dommages-ouvrage, RC pro de l'agence, assurances voyageurs.
- Souscription intégrée (offres partenaires), contrôle des échéances et attestations.
- **Gestion des sinistres** : déclaration (dégât des eaux, incendie, vol, catastrophe naturelle), constats amiables (dégâts des eaux), expertise, devis, indemnisation, travaux, suivi des délais, refacturation.
- Statistiques de sinistralité par immeuble.

---

## 19. Module 16 — Fiscalité et déclarations

- Préparation des **données de déclaration de revenus fonciers** (régime réel/micro), revenus meublés (BIC), avec ventilation des charges déductibles, intérêts d'emprunt, amortissements (LMNP), déficits.
- Attestations fiscales annuelles pour chaque propriétaire.
- Déclarations liées aux biens (occupation, taxes locales), taxe de séjour (saisonnier), retenues à la source et attestations pour non-résidents.
- Plus-values immobilières : simulation (abattements pour durée de détention) pour l'aide à la décision de vente.
- Fiscalité des transactions : droits d'enregistrement, frais d'acte, TVA immobilière (neuf, terrains à bâtir).
- Paramétrage multi-pays des règles fiscales.

---

## 20. Module 17 — Intelligence artificielle et automatisations

- **Moteur de workflows** sans code : déclencheurs (date, événement, statut), conditions, actions (document, notification, tâche, paiement, appel API), validations.
- **Assistants IA** :
  - rédaction d'annonces, de courriers, de comptes rendus ;
  - lecture et extraction automatique de documents (factures, baux, titres, pièces d'identité, avis d'imposition) ;
  - détection de fraude documentaire ;
  - pré-qualification des tickets et suggestion de prestataire à partir de photos ;
  - chatbot multilingue 24/7 pour locataires, propriétaires et prospects (escalade vers un humain) ;
  - estimation automatique (AVM) des loyers et prix ;
  - scoring de risque d'impayé, de départ locataire, de vacance ;
  - lettrage des paiements non identifiés ;
  - recommandation d'arbitrage patrimonial (vendre / rénover / relouer) ;
  - résumé d'un dossier avant appel client.
- **Garde-fous IA** : validation humaine des décisions à impact (sélection de locataire, retenues sur dépôt), explicabilité, absence de critères discriminatoires, traçabilité des suggestions.
- **IoT** (option) : serrures connectées, détecteurs de fuite, compteurs communicants, capteurs de température/humidité pour prévention des sinistres et de l'humidité.

---

## 21. Module 18 — Administration, sécurité et paramétrage

- Multi-tenant (plusieurs agences/franchises), multi-sociétés, multi-pays, multi-devises (avec taux de change), multi-langues (FR, EN, …).
- Paramétrage : modèles de documents (éditeur avec champs de fusion), barèmes d'honoraires, indices, plan comptable, taxes, workflows, notifications, statuts, champs personnalisés, chartes graphiques (marque blanche pour partenaires).
- Gestion des utilisateurs, rôles, équipes, délégations, SSO (SAML/OIDC), **authentification multifacteur** obligatoire pour les rôles sensibles.
- **Journal d'audit** complet et inaltérable, exportable.
- Sauvegardes, PRA/PCA, environnement de test (sandbox).
- Gestion des imports/migrations depuis d'autres logiciels (reprise des données).
- Gestion des abonnements et de la facturation SaaS.

---

## 22. Intégrations externes

| Domaine | Intégrations |
|---|---|
| Banques | Flux bancaires (EBICS, open banking/DSP2), SEPA SCT/SDD, IBAN virtuels, comptes séquestres |
| Paiement | Cartes (PSP), mobile money (Orange Money, MTN MoMo, Wave, Moov, M-Pesa), agrégateurs locaux |
| Signature & recommandé | Prestataires de signature électronique et de LRE |
| Portails d'annonces | Portails immobiliers nationaux et locaux, réseaux sociaux |
| Location courte durée | Plateformes de réservation, channel managers |
| Données | Bases de transactions publiques, cadastre, cadastre/SIG, géocodage, indices (IRL/ILC/ILAT ou locaux), registres des entreprises |
| Identité & conformité | KYC/vérification d'identité, listes de sanctions/PPE, dossiers locataires certifiés, vérification fiscale |
| Garanties & assurances | Visale, assureurs GLI/PNO/MRH, courtiers |
| Comptabilité | Logiciels comptables (export FEC, API) |
| Énergie & compteurs | Fournisseurs d'énergie, télérelève |
| Communication | E-mail, SMS, WhatsApp Business, téléphonie/VoIP, visioconférence |
| Agenda | Google Calendar, Outlook |
| Notaires / géomètres | Échange de pièces, plateformes notariales, prise de RDV de signature |
| IoT | Serrures et boîtes à clés connectées, capteurs |
| API ouverte | API REST/GraphQL documentée + webhooks pour partenaires et institutionnels |

---

## 23. Exigences non fonctionnelles

- **Sécurité** : chiffrement en transit (TLS 1.2+) et au repos, gestion des secrets, MFA, cloisonnement des données par tenant, tests d'intrusion réguliers, conformité ISO 27001 / SOC 2 visée, journalisation, détection d'anomalies, protection anti-fraude au RIB.
- **Disponibilité** : 99,9 % visé, PRA (RPO ≤ 1 h, RTO ≤ 4 h), sauvegardes chiffrées multi-sites.
- **Performance** : temps de réponse < 2 s pour 95 % des écrans, traitements de masse (quittancement de 100 000 lots) en tâches asynchrones.
- **Scalabilité** : architecture cloud élastique (microservices ou monolithe modulaire bien découpé), file de messages pour les événements métier.
- **Accessibilité** : WCAG 2.1 AA, responsive, PWA, mode hors-ligne pour l'app terrain.
- **Faible connectivité** : optimisation des images, synchronisation différée, USSD/SMS pour paiements et notifications dans les zones à faible couverture.
- **Hébergement et souveraineté** : localisation des données conforme à la réglementation du pays.
- **Qualité** : tests automatisés, intégration continue, environnements de recette, monitoring, observabilité.
- **Réversibilité** : export complet des données client dans un format ouvert.

---

## 24. Modèle de données

Entités principales et relations essentielles :

| Entité | Relations clés |
|---|---|
| Tiers (personne physique / morale) | rôles multiples : mandant, locataire, garant, acquéreur, vendeur, prestataire, apporteur |
| Portefeuille | appartient à un ou plusieurs mandants |
| Site / Immeuble | contient des lots ; lié à une copropriété |
| Lot / Bien / Parcelle | appartient à des propriétaires (quotes-parts, démembrement) ; a des équipements, compteurs, diagnostics, médias |
| Mandat | lie un mandant à des lots ; porte la grille d'honoraires |
| Annonce | publie un lot pour location ou vente |
| Candidature / Dossier | candidat ↔ lot ↔ pièces ↔ score |
| Bail | lot(s) ↔ locataire(s) ↔ garant(s) ; conditions financières, indices, échéances |
| État des lieux | bail ↔ pièces ↔ éléments ↔ photos |
| Échéance / Appel / Quittance | bail ↔ montants ↔ paiements |
| Paiement / Mouvement bancaire | lettré à des échéances ou factures |
| Écriture comptable | comptes mandant, locataire, fournisseur, agence |
| Reversement | mandant ↔ période ↔ CRG |
| Ticket / Intervention / Ordre de service | lot ↔ demandeur ↔ prestataire ↔ devis ↔ facture |
| Projet de travaux | lots ↔ budget ↔ lots de travaux |
| Affaire de vente | mandat vente ↔ acquéreurs ↔ visites ↔ offres ↔ compromis ↔ acte |
| Lotissement / Programme | parcelles/lots ↔ réservations ↔ échéanciers |
| Police d'assurance / Sinistre | lot/immeuble ↔ assureur ↔ indemnisation |
| Dossier contentieux | bail/tiers ↔ procédure ↔ frais |
| Document | rattachable à toute entité ; versions ; signatures |
| Événement d'audit | toute entité ↔ utilisateur ↔ horodatage ↔ diff |

---

## 25. Modèle économique

| Source de revenus | Détail |
|---|---|
| Honoraires de gestion locative | % des encaissements (typiquement 5 à 10 % HT selon marché) ou forfait par lot |
| Honoraires de mise en location | Plafonnés réglementairement, partagés bailleur/locataire |
| Honoraires de transaction | % du prix (bâti / terrain) ou forfait |
| Commercialisation programmes / lotissements | Commission sur ventes, frais de gestion des échéanciers |
| Services additionnels | EDL, gestion des travaux (% du montant), déclarations fiscales, conciergerie, home staging, photos |
| Assurances | Commissions de courtage GLI, PNO, MRH |
| Location saisonnière | 15 à 25 % des revenus + frais de ménage |
| SaaS / marque blanche | Abonnement pour agences et partenaires utilisant la plateforme |
| Services financiers | Avance de loyers garantis, partenariats crédit immobilier |

---

## 26. Feuille de route

| Phase | Contenu | Objectif |
|---|---|---|
| **MVP (0–6 mois)** | Référentiel biens, tiers, mandats de gestion, baux, quittancement, encaissement (virement, carte, mobile money), comptabilité mandant de base, reversements, CRG, espace propriétaire et locataire, tickets simples, GED, e-signature | Gérer les premiers portefeuilles en transparence |
| **V1 (6–12 mois)** | Commercialisation locative (annonces, multidiffusion, candidatures, scoring), EDL mobile, régularisation des charges, révisions automatiques, recouvrement automatisé, module transaction bâti (estimation, mandats, acquéreurs, offres, suivi), CRM | Couvrir le cycle complet location + vente |
| **V2 (12–18 mois)** | Module terrains et lotissements (SIG, ventes à tempérament), travaux et prestataires avancés, assurances et sinistres, contentieux, fiscalité, reporting avancé, API partenaires | Partenaires/institutionnels et promoteurs |
| **V3 (18–24 mois)** | Location saisonnière/channel manager, syndic, IA avancée (AVM, scoring, chatbot), IoT, marketplace de services, multi-pays complet | Différenciation et passage à l'échelle |

---

## 27. Indicateurs clés (KPI)

**Gestion locative** : taux d'occupation physique/financier · délai moyen de relocation · taux d'impayés (à 30/60/90 j) · taux de recouvrement · délai de reversement aux propriétaires · délai de restitution des dépôts · délai de résolution des tickets · coût de maintenance par lot · taux de rotation des locataires · NPS propriétaires et locataires · lots gérés par gestionnaire.

**Transaction** : nombre de mandats (dont exclusifs) · délai moyen de vente · écart prix affiché/prix de vente · taux de transformation visite → offre → vente · CA honoraires · taux de chute des compromis.

**Terrains/lotissements** : rythme d'écoulement des parcelles · taux de recouvrement des échéanciers · délai d'obtention des titres individuels.

**Plateforme** : taux d'adoption des portails, part des paiements en ligne, part des documents signés électroniquement, taux d'automatisation (opérations sans intervention humaine), disponibilité.

---

## 28. Annexes

### 28.1 Statuts types
- **Lot** : Brouillon → Disponible → En commercialisation → Réservé → Loué → En préavis → En travaux → En vente → Vendu → Archivé.
- **Candidature** : Reçue → Incomplète → Complète → En analyse → Présentée au propriétaire → Acceptée / Refusée → Bail signé.
- **Bail** : Brouillon → En signature → Signé → Actif → En préavis → Terminé → Soldé → Archivé (+ Contentieux).
- **Ticket** : Nouveau → Qualifié → En attente devis → En attente validation → Planifié → En cours → Réalisé → Facturé → Clôturé.
- **Affaire de vente** : Estimation → Mandat signé → En diffusion → Offre reçue → Offre acceptée → Compromis signé → Conditions levées → Acte signé → Honoraires encaissés.
- **Parcelle** : Disponible → Optionnée → Réservée → En paiement échelonné → Soldée → Titre muté → Livrée.

### 28.2 Calendrier annuel automatisé de la gestion
| Période | Tâches générées |
|---|---|
| Chaque mois | Appels de loyers, encaissements, relances, reversements, CRG |
| Date anniversaire du bail | Révision du loyer, relance attestation d'assurance |
| Annuel (après clôture des comptes syndic) | Régularisation des charges |
| Annuel | Taxe foncière, refacturation TEOM, attestations fiscales, revue des mandats, entretien chaudière |
| Échéances | Fin de bail, diagnostics, polices d'assurance, documents prestataires, contrôles réglementaires |

### 28.3 Checklist « Confier mon bien » (pièces propriétaire)
Pièce d'identité · justificatif de domicile · titre de propriété / titre foncier · RIB · diagnostics · règlement de copropriété et derniers PV d'AG · dernier avis de taxe foncière · attestation PNO · bail en cours et EDL (si loué) · décompte du syndic · factures de travaux récents · contrats d'entretien · clés (nombre, types) · statuts et Kbis (personne morale) · pouvoirs (indivision, mandat).

### 28.4 Checklist dossier de vente terrain
Titre foncier ou acte de propriété · certificat de propriété / état des droits réels récent · plan de bornage et procès-verbal · plan de situation · certificat d'urbanisme · identité de tous les ayants droit · quitus fiscal · autorisation de lotir/morceler (si applicable) · attestation de non-litige · photos/drone et coordonnées GPS des bornes.

### 28.5 Points de vigilance de l'expert
1. **La comptabilité mandant est le cœur de la confiance** : sans représentation des fonds irréprochable et rapprochement quotidien, aucune transparence n'est crédible.
2. **Paramétrer la réglementation par pays** plutôt que la coder en dur (indices, délais de préavis, plafonds d'honoraires, durées de restitution du dépôt, trêves).
3. **Anti-fraude** : faux dossiers locataires, faux RIB fournisseurs/propriétaires, doubles ventes de terrains — prévoir des contrôles systématiques.
4. **Mobile-first et paiement mobile** dans les marchés où la bancarisation est faible.
5. **Validation par le propriétaire en un clic** : c'est ce qui réduit le plus les délais et augmente la satisfaction.
6. **Reprise de données** soignée : c'est le premier frein à l'adoption par les partenaires qui migrent leurs portefeuilles.
7. **Ne pas tout livrer d'un coup** : un MVP centré sur le triptyque *bail → encaissement → reversement transparent* crée la valeur la plus visible.
