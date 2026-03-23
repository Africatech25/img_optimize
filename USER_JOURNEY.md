# 🗺️ Parcours Utilisateur - Image Optimizer

Guide complet du parcours utilisateur dans l'application Image Optimizer.

---

## 📍 1. LANDING PAGE (`/`)

### Première impression
L'utilisateur arrive sur une **landing page moderne et attractive** avec :

- **Hero section** au-dessus de la ligne de flottaison :
  - Titre accrocheur : "Optimisez vos images en quelques secondes"
  - Sous-titre expliquant les bénéfices (SEO, performance, légèreté)
  - Bouton CTA **"Commencer l'optimisation"** en gradient violet-cyan
  - Illustration animée avec mockup de l'interface

### Points clés à transmettre
1. **Objectif clair** : Optimisation d'images pour le web
2. **Promesse** : Réduction de taille importante + Conservation de qualité
3. **Avantage** : 100% local, aucune donnée envoyée sur internet
4. **Call-to-action** : Incite à tester immédiatement

### Sections informatives

#### 🎯 Section 2 - Fonctionnalités (4 cards)
- **Compression intelligente** (🗜️)
  - "Réduction jusqu'à 80% du poids sans perte visible"
  - Rassure sur la qualité préservée

- **Formats modernes** (⚡)
  - "JPEG, WebP, AVIF, PNG au choix"
  - Montre la flexibilité

- **100% local** (🔒)
  - "Aucune donnée envoyée sur internet"
  - Critère de confiance/sécurité

- **Renommage SEO** (🏷️)
  - "Nommage automatique optimisé pour Google"
  - Avantage supplémentaire

#### 📊 Section 3 - Comparaison des formats
Tableau interactif avec :

| Format | Poids | Qualité | Support | Idéal pour |
|--------|-------|---------|---------|-----------|
| JPEG | Moyen | Bonne | 100% | Photos, images complexes |
| **WebP** ⭐ | Léger | Excellente | 97% | Usage universel web |
| AVIF | Ultra-léger | Excellente | 90% | Sites modernes |
| PNG | Lourd | Sans perte | 100% | Logos, transparence |

**Aide à la décision** : WebP recommandé par défaut

#### 🎬 Section 4 - Comment ça marche (3 étapes)
Flow visuel simple :
1. **Dépose tes images** → Zone drag & drop
2. **Choisis tes paramètres** → Préfixe, format, qualité
3. **Télécharge le résultat** → ZIP prêt à l'emploi

### Navigation
- **Bouton principal** : "Commencer l'optimisation" → `/app`
- **Footer minimaliste** : Nom de l'outil

---

## 🎯 2. INTERFACE D'OPTIMISATION (`/app`)

### Layout général
**2 colonnes sur desktop** (responsive sur mobile) :
- **Colonne gauche** (25%) : Panneau de paramètres (sticky)
- **Colonne droite** (75%) : Zone d'images + résultats

### 📋 Colonne gauche - Paramètres

#### 1. Préfixe SEO (obligatoire)
```
Préfixe SEO *
[hotel-bretagne-2026]
↳ Ce préfixe sera utilisé pour nommer vos images
```
- **Aide** : Explique le rôle du préfixe
- **Validation** : Le bouton "Optimiser" est disabled si vide

#### 2. Format de sortie
```
Format de sortie
[WebP ▼]

🟢 WebP — 30-50% plus léger que JPEG, 97% navigateurs ⭐
```
- **Description dynamique** selon le format choisi
- **Options** : JPEG, WebP, AVIF, PNG
- **Effet** : Change la description + plage de qualité

#### 3. Slider de qualité
```
Qualité                                            [##########-]  70
Range: 1 ← → 100

Slider fluide avec positions repère
```
- **Dynamique** : Change selon le format
  - JPEG : 1–95 (défaut 65)
  - WebP : 1–100 (défaut 70)
  - AVIF : 1–100 (défaut 65)
  - PNG : 1–9 (défaut 7, "Niveau de compression")

- **Feedback visuel** : Nombre affiché en temps réel

#### 4. Numéro de départ
```
Numéro de départ
[1]
↳ Influence la numérotation des fichiers de sortie
```

#### 5. Bouton d'optimisation
```
┌─────────────────────────┐
│ Optimiser les images    │ ← Gradient violet-cyan
└─────────────────────────┘
```
- **State enabled** : Au moins 1 image + préfixe non-vide
- **State disabled** : Aucune image OU préfixe vide
- **Pendant traitement** : "Optimisation en cours..." (disabled)

---

### 🖼️ Colonne droite - Zone d'images

#### État vide
```
┌──────────────────────────────────────┐
│   Images à optimiser (0)             │
│   [+ Ajouter des images]             │
│                                      │
│   Glisse-dépose tes images ici       │
│   ou clique sur "Parcourir"          │
│                                      │
│   JPG • PNG • WebP • BMP • TIFF      │
└──────────────────────────────────────┘
```

#### Drag & drop
- **Zone active** : Surlignée au survol (border violet)
- **Feedback** : Animation légère de scale
- **Formats acceptés** : JPG, JPEG, PNG, WebP, BMP, TIFF

#### Grille de miniatures (après upload)
```
┌─────────┐  ┌─────────┐  ┌─────────┐
│  [img]  │  │  [img]  │  │  [img]  │
│   ✕    │  │   ✕    │  │   ✕    │
│ photo.jpg │  │image.png │  │pic.bmp   │
│  2.5 Mo   │  │ 1.8 Mo   │  │ 3.2 Mo   │
├─────────┤  ├─────────┤  ├─────────┤
│hotel-2026│  │hotel-2027│  │hotel-2028│
│-01.webp  │  │-02.webp  │  │-03.webp  │
└─────────┘  └─────────┘  └─────────┘
```

**Pour chaque image :**
- Aperçu visuel (thumbnail)
- Nom du fichier original
- Poids original en Mo/Ko
- **Bouton ✕** : Supprimer de la liste (x)
- **Badge futur nom** : Nom SEO post-optimisation

**Interactions :**
- Hover sur image : Affiche bouton supprimer plus visible
- Click ✕ : Retire image instantanément
- Click "+ Ajouter des images" : Ouvre file picker

---

## ⚙️ 3. PHASE DE TRAITEMENT

### Démarrage
1. User clique **"Optimiser les images"**
2. Frontend envoie FormData (fichiers + params) vers `/api/optimize`
3. Backend crée un job avec UUID et retourne `job_id`
4. Frontend démarre timer d'actualisation de progression

### Interface de progression

#### Barre de progression globale
```
Progression
4 / 12 images

████████░░░░░░░░░░░░░░░░░ 33%
```
- Mise à jour en temps réel via SSE
- Animée et fluide

#### Log de progression (temps réel via SSE)
```
00:00:52

✅ photo1.jpg           2.4 Mo → 1.1 Mo  [↓54%]
✅ photo2.jpg           1.8 Mo → 0.9 Mo  [↓50%]
⏳ photo3.jpg           Traitement...
```

Pour chaque image :
- **✅ OK** : Image traitée avec succès
- **⏳ En cours** : Barre de progression mini
- **⚠️ Erreur** : Message d'erreur avec détails
- **Affichage** :
  - Nom du fichier original
  - Tailles avant/après
  - Pourcentage de réduction

#### Miniatures mises à jour
```
┌─────────┐
│ [✓img]  │  ← Fond teinté vert "traité"
│ 2.4 Mo  │
└─────────┘
```
Les images traitées passent visuellement à l'état "complété"

---

## 📊 4. RÉSUMÉ FINAL (Après optimisation)

### Résumé statistique

#### Card résumé principal
```
✓ Optimisation terminée !
12 images optimisées avec succès

┌─────────────────┬──────────────┬──────────────┐
│   Images        │ Réduction    │ Espace écono │
│    optimisées   │ moyenne      │              │
│      12         │   52%        │  15.5 Mo     │
└─────────────────┴──────────────┴──────────────┘
```

#### Comparison visuelle taille
```
Comparaison des tailles

Avant:  [████████████████████████████] 31.2 Mo
Après:  [████████████████░░░░░░░░░░░░] 15.7 Mo
        ↓ 49.7% de réduction
```

#### Statistiques détaillées
- Nombre d'images optimisées
- Taille totale avant/après
- Réduction en pourcentage
- Erreurs rencontrées (si ex)

### Actions finales

#### Bouton principal
```
┌──────────────────────┐
│ Télécharger le ZIP   │ ← Gradient vert
└──────────────────────┘
```
- Déclenche téléchargement ZIP
- Fichier : `optimized-images-{job_id}.zip`
- Contient toutes les images optimisées

#### Bouton secondaire
```
┌──────────────────────┐
│ Nouvelle optimisation │ ← Outline
└──────────────────────┘
```
- Remet tout à zéro
- Retour à l'interface vierge
- Efface les images uploaddées

---

## 🔄 5. PARCOURS RAPIDE (Happy Path)

### Scénario optimal
```
1. Arrive sur landing page
   ↓ [Voit présentation attrayante]
2. Clique "Commencer l'optimisation"
   ↓ Navigue vers /app
3. Remplit paramètres
   - Préfixe : "hotel-bretagne-2026"
   - Format : WebP (défaut)
   - Qualité : 70 (défaut)
   - Numéro : 1
4. Glisse-dépose 5 images JPG
   ↓ [Voit miniatures s'afficher]
5. Clique "Optimiser les images"
   ↓ [Voit progression en temps réel]
6. Attend 30-60 sec (selon taille)
   ↓ [Voit résumé final]
7. Clique "Télécharger le ZIP"
   ↓ [Récupère 5 images webp optimisées]
8. ✅ FIN - Images prêtes pour le web
```

**Durée totale** : 2-3 minutes

---

## ⚠️ 6. CAS D'ERREURS

### Image invalide
```
❌ photo-corrompue.jpg
   Erreur: Format d'image non supporté

[✕] Retirer cette image
```
- User peut supprimer et réessayer
- Les autres images continuent à traiter

### Erreur réseau
```
Erreur: Impossible de se connecter au serveur
[↻ Réessayer] [Retour à l'accueil]
```

### Image trop grosse
```
⚠️ photo-4K.jpg           8.2 Mo
   Fichier trop volumineux pour le traitement
```

---

## 🎨 7. ÉTATS VISUELS

### Couleurs
- **Violet/Cyan** : Accents, CTA, gradients
- **Vert** : Succès, complété
- **Rouge** : Erreurs
- **Slate** : Fond dark mode

### Transitions
- Fade-in : Apparition d'éléments
- Slide-up : Animations d'entrée
- Scale : Hover sur cards et boutons
- Pulse : Indicateurs de progression

### Typographie
- **Inter** : Police principale
- **Headings** : Bold, grande taille
- **Corps** : Slate-400 (bon contraste)

---

## 📱 8. RESPONSIVE (Mobile)

### Sur téléphone
- **1 colonne** (stack vertical)
- Paramètres au-dessus, images dessous
- Bouton "Optimiser" full-width
- Grille : 2 colonnes d'images
- Miniatures plus petites

### Sur tablette
- **2 colonnes** version réduite
- Paramètres : 30% de la largeur
- Images : 70% de la largeur

---

## 🏁 RÉSUMÉ DU JOURNEY

```
Landing (présentation)
        ↓ [CTA]
Optimizer (paramétrisation)
        ↓ [Drag & drop images]
Images uploadées (preview)
        ↓ [Bouton optimiser]
Traitement (progression SSE)
        ↓ [100% complété]
Résumé final (stats + ZIP)
        ↓ [Télécharger]
Images téléchargées ✅
```

---

## 🎯 POINTS CLS DE CONVERSION

1. **Landing** > Accrocheur, bénéfices clairs
2. **Paramètres** > Simples, valeurs par défaut bonnes
3. **Upload** > Drag & drop intuitif
4. **Progression** > Visibilité temps réel
5. **Résultat** > Métriques impressionnantes (50% réduction)
6. **Téléchargement** > One-click, prêt à l'emploi

---

**Durée moyenne du parcours complet : 2-3 minutes** ⏱️
