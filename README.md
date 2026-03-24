# 🚀 ImgOpt : Optimiseur d'Images Ultra-Performant

**ImgOpt** est une application web moderne conçue pour compresser et convertir vos images massivement sans compromis sur la qualité. Optimisé pour le SEO et la performance web, l'outil supporte les formats de nouvelle génération : **WebP** et **AVIF**.

---

## 📖 Sommaire
1. [Utilisation (Pour tous)](#-utilisation-pour-tous)
2. [Formats de Sortie supportés](#-formats-de-sortie-supportés)
3. [Architecture Technique](#-architecture-technique)
4. [Installation Locale (Développeurs)](#-installation-locale-développeurs)
5. [API & Endpoints](#-api--endpoints)
6. [Déploiement](#-déploiement)
7. [Sécurité & Confidentialité](#-sécurité--confidentialité)

---

## 🎨 Utilisation (Pour tous)

L'utilisation est simple et intuitive :
1.  **Glissez-déposez** vos images (JPG, PNG) dans la zone centrale.
2.  **Choisissez le format** souhaité parmi les options disponibles.
3.  **Ajustez la qualité** (70-80% est recommandé pour un équilibre parfait).
4.  **Renommez vos fichiers** (Optionnel) : Utile pour le SEO (ex: `produit-ete-`).
5.  **Lancez l'optimisation**.
6.  **Téléchargez** le fichier ZIP contenant tous vos assets optimisés.

---

## 🖼 Formats de Sortie supportés

ImgOpt vous permet de convertir vos images vers les standards les plus récents :

| Format | Avantages | Recommandation |
| :--- | :--- | :--- |
| **WebP** | Excellent rapport qualité/poids, supporté par 96%+ des navigateurs. | **Choix par défaut** pour le web moderne. |
| **AVIF** | Compression supérieure au WebP (jusqu'à 30% de gain en plus). | Pour un maximum de performance (si activé sur le serveur). |
| **JPEG** | Compatibilité universelle absolue. | Pour les impressions ou les vieux systèmes. |
| **PNG** | Supporte la transparence sans perte. | Pour les logos et graphiques avec fond transparent. |

> [!NOTE]
> Tous les fichiers optimisés sont regroupés dans une **archive ZIP** unique afin de faciliter le téléchargement et l'organisation de vos projets.

---

## 🛠 Architecture Technique

L'application est séparée en deux parties distinctes :

-   **Frontend** : Développé avec **React** et **Vite.js**. Il utilise **Tailwind CSS** pour une interface "Glassmorphism" moderne et ultra-fluide.
-   **Backend** : Une API robuste développée avec **FastAPI (Python)**. Elle utilise la bibliothèque **Pillow** et des plugins spécialisés pour un traitement d'image haute performance.
-   **Gestion des Formats (Smart Detection)** : Le frontend interroge dynamiquement le backend (`/api/config`) pour savoir quels formats sont réellement supportés par le serveur (ex: AVIF). Si un plugin est manquant sur le serveur, le format est automatiquement masqué dans l'interface utilisateur pour éviter toute erreur.
-   **Analytics** : Intégration de **Vercel Analytics** pour un suivi anonyme des performances.

---

## 💻 Installation Locale (Développeurs)

### Prérequis
-   Python 3.11+
-   Node.js 18+
-   npm ou yarn

### 1. Cloner le projet
```bash
git clone https://github.com/Africatech25/img_optimize.git
cd img_optimize
```

### 2. Configurer le Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Le backend tournera sur `http://localhost:8000`.

### 3. Configurer le Frontend
```bash
cd ../frontend
npm install
npm run dev
```
Le frontend sera accessible sur `http://localhost:5173`.

---

## 🔌 API & Endpoints

L'API est documentée automatiquement via Swagger à l'adresse `/docs`.

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/config` | Retourne la configuration (formats supportés). |
| `POST` | `/api/optimize` | Envoie les images pour traitement (Multipart). |
| `GET` | `/api/job/{id}` | Suit l'avancement d'un job d'optimisation (SSE). |
| `GET` | `/api/download/{id}` | Télécharge le pack ZIP final. |

---

## 🚀 Déploiement

### Backend (Render)
1.  Créer un "Web Service".
2.  Build Command : `pip install -r requirements.txt`.
3.  Start Command : `uvicorn main:app --host 0.0.0.0 --port $PORT`.

### Frontend (Vercel)
1.  Connecter le repo GitHub.
2.  Root directory : `frontend`.
3.  Variable d'env : `VITE_API_URL` (URL de votre API Render).

---

## 🛡 Sécurité & Confidentialité

-   **Zéro Stockage Persistant** : Les images sont traitées en mémoire vive et supprimées immédiatement.
-   **HTTPS Partout** : Toutes les données transitent via des tunnels chiffrés.
-   **Anonymat** : Aucun compte requis. Pas de cookies de tracking publicitaire.

---

**Développé par Maurice CODJO**
