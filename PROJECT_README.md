# 🖼️ Image Optimizer - Application Web

Une application web locale moderne et élégante pour optimiser vos images pour le web. Conversion en JPEG, WebP, AVIF ou PNG avec compression intelligente, renommage SEO automatique et suivi en temps réel.

![Image Optimizer](https://img.shields.io/badge/React-18-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green) ![Tailwind](https://img.shields.io/badge/TailwindCSS-3-cyan)

## ✨ Fonctionnalités

- **🎨 Interface moderne** - Landing page attractive + interface d'optimisation intuitive
- **🗜️ Compression intelligente** - Réduction jusqu'à 80% du poids sans perte visible
- **📏 Limite stricte de 1 Mo** - Toutes les images optimisées respectent un maximum de 1 Mo
- **⚡ Formats modernes** - JPEG, WebP, AVIF, PNG au choix
- **📡 Progression en temps réel** - Server-Sent Events (SSE) pour un suivi live
- **🏷️ Renommage SEO** - Nommage automatique optimisé pour Google
- **✍️ Branding & Signature** - Apposez logo ou texte pour protéger et marquer vos créations
- ** 100% local** - Aucune donnée envoyée sur internet
- **🌙 Dark mode élégant** - Interface moderne avec Tailwind CSS

## 📁 Structure du projet

```
img_optimize/
├── backend/
│   ├── main.py                 # Serveur FastAPI avec SSE
│   ├── optimize_images.py      # Script d'optimisation
│   └── requirements.txt        # Dépendances Python
└── frontend/
    ├── index.html
    ├── vite.config.js          # Config Vite avec proxy API
    ├── tailwind.config.js      # Config Tailwind
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx             # Routing React Router
        ├── index.css           # Styles Tailwind
        ├── pages/
        │   ├── Landing.jsx     # Page d'accueil
        │   └── Optimizer.jsx   # Interface d'optimisation
        └── components/
            ├── DropZone.jsx        # Zone drag & drop
            ├── ImageGrid.jsx       # Grille d'images
            ├── ParamsPanel.jsx     # Panneau de paramètres
            ├── ProgressLog.jsx     # Log de progression
            └── ResultCard.jsx      # Résumé final
```

## 🚀 Démarrage rapide

### Prérequis

- Python 3.8+
- Node.js 16+
- npm ou yarn

### 1️⃣ Installation et démarrage du backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Le serveur FastAPI démarre sur **http://localhost:8000**

> **Note AVIF** : Pour activer le format AVIF, installez le plugin :
> ```bash
> pip install pillow-avif-plugin
> ```

### 2️⃣ Installation et démarrage du frontend

Dans un nouveau terminal :

```bash
cd frontend
npm install
npm run dev
```

Le frontend Vite démarre sur **http://localhost:5173**

### 3️⃣ Accès à l'application

Ouvrez votre navigateur sur : **http://localhost:5173**

## 🎯 Utilisation

### Page d'accueil (/)

- Landing page moderne présentant les fonctionnalités
- Comparaison des formats JPEG / WebP / AVIF / PNG
- Explication du processus en 3 étapes
- Bouton CTA vers l'interface d'optimisation

### Interface d'optimisation (/app)

#### Colonne gauche - Paramètres

1. **Préfixe SEO** (obligatoire) - Ex: `hotel-bretagne-2026`
2. **Format de sortie** - JPEG / WebP / AVIF / PNG
3. **Qualité** - Slider dynamique selon le format :
   - JPEG : 1–95 (défaut 65)
   - WebP : 1–100 (défaut 70)
   - AVIF : 1–100 (défaut 65)
   - PNG : 1–9 (défaut 7, niveau de compression)
4. **Numéro de départ** - Pour la numérotation (défaut : 1)
5. **⚠️ Limite de taille** - Toutes les images seront compressées jusqu'à **max 1 Mo** obligatoirement

#### Colonne droite - Zone d'images

- **Drag & drop** ou bouton "Parcourir"
- **Formats acceptés** : JPG, JPEG, PNG, WebP, BMP, TIFF
- **Grille de miniatures** avec :
  - Aperçu visuel
  - Nom et poids original
  - Badge du futur nom SEO (ex: `hotel-2026-01.webp`)
  - Bouton de suppression

#### Pendant le traitement

- **Barre de progression** globale animée
- **Log en temps réel** via SSE :
  - Chaque image traitée avec son nom
  - Poids avant → après
  - Pourcentage de gain
  - Icône ✅ ou ⚠️

#### Résumé final

- Nombre d'images optimisées
- Poids total avant → après
- Réduction moyenne en %
- **Vérification** : Toutes les images sont ≤ 1 Mo
- **Bouton "Télécharger le ZIP"**
- **Bouton "Nouvelle optimisation"**

## 🔧 Architecture technique

### Backend (FastAPI)

- **Route POST `/api/optimize`** - Démarre un job d'optimisation, retourne un `job_id`
- **Route GET `/api/progress/{job_id}`** - Stream SSE de la progression
- **Route GET `/api/download/{job_id}`** - Télécharge le ZIP des images optimisées
- **Route GET `/api/formats`** - Liste des formats disponibles avec config
- **Nettoyage automatique** - Suppression des fichiers > 10 minutes
- **Traitement asynchrone** - `asyncio` pour ne pas bloquer le serveur

### Frontend (React + Vite)

- **React Router v6** - Routing entre Landing et Optimizer
- **Tailwind CSS** - Styling complet (dark mode)
- **Lucide React** - Icônes modernes
- **EventSource natif** - Consommation du SSE
- **Fetch natif** - Appels API (pas d'Axios)
- **Proxy Vite** - `/api` → `http://localhost:8000`

## 🎨 Design

- **Palette** : Dark mode avec accents violet et cyan
- **Typographie** : Inter (Google Fonts)
- **Animations** : Transitions subtiles, hover effects
- **Responsive** : Stack mobile, 2 colonnes desktop

## 📝 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/health` | GET | Health check + formats disponibles |
| `/api/formats` | GET | Liste des formats avec config |
| `/api/optimize` | POST | Démarre l'optimisation (multipart/form-data) |
| `/api/progress/{job_id}` | GET | Stream SSE de progression |
| `/api/job/{job_id}` | GET | Statut d'un job |
| `/api/download/{job_id}` | GET | Télécharge le ZIP |
| `/api/cleanup/{job_id}` | DELETE | Nettoie un job |

## 🐛 Dépannage

### Le backend ne démarre pas

- Vérifiez que Python 3.8+ est installé
- Assurez-vous que le port 8000 est libre

### Le frontend ne se connecte pas au backend

- Vérifiez que le backend est bien démarré
- Vérifiez la config proxy dans `vite.config.js`

### AVIF non disponible

Installez le plugin :
```bash
pip install pillow-avif-plugin
```

## 📄 Licence

Projet personnel - Libre d'utilisation

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une PR.

---

**Fait avec ❤️ en Python et React**
