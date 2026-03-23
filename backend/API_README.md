# 🖼️ ImgOpt API - Documentation Technique Detailed

Bienvenue dans la documentation officielle de l'API **ImgOpt**. Ce service est conçu pour l'optimisation massive d'images, le renommage SEO et la conversion vers des formats de nouvelle génération (WebP, AVIF).

## 🚀 Vue d'Ensemble

L'API est construite avec **FastAPI** (Python 3.10+) et repose sur un moteur de traitement asynchrone pour garantir une réactivité maximale, même sous une charge importante de fichiers.

### Caractéristiques principales :
- **Traitement Asynchrone** : Les images sont traitées en arrière-plan via des tâches non-bloquantes.
- **Suivi Temps Réel (SSE)** : Notification instantanée de la progression via *Server-Sent Events*.
- **Optimisation SEO** : Renommage automatique et intelligent des fichiers avec indexation personnalisée.
- **Formats Supportés** : WebP (perte/sans perte), AVIF, JPEG progressif, PNG optimisé.
- **Sécurité** : Cycle de nettoyage automatique des fichiers temporaires toutes les 24 heures.

---

## 🛠️ Endpoints de Référence

### 1. Diagnostics et Configuration

#### `GET /api/health`
Vérifie l'état de santé du service et l'état des dépendances système (moteurs de compression).
- **Réponse :** `200 OK`
- **Body :**
  ```json
  {
    "status": "ok",
    "avif_available": true,
    "formats": ["webp", "avif", "jpeg", "png"]
  }
  ```

#### `GET /api/formats`
Récupère les métadonnées et les plages de configuration pour chaque codec supporté.
- **Réponse :** `200 OK`
- **Contenu :** Descriptions, valeurs de qualité par défaut et limites (1-100).

---

### 2. Le Pipeline d'Optimisation

#### `POST /api/optimize`
C'est le point d'entrée principal. Il initialise un **Job d'optimisation**.

**Paramètres (Form-Data) :**
| Champ | Type | Obligatoire | Description |
| :--- | :--- | :--- | :--- |
| `files` | binary[] | Oui | Liste d'images (multi-upload supporté) |
| `format` | string | Non | Codec cible : `webp` (défaut), `avif`, `jpeg`, `png` |
| `quality` | integer | Non | Niveau de qualité (dépend du format) |
| `prefix` | string | Oui | Racine du nom de fichier (ex: `chaussures-sport-rouge`) |
| `start_number` | integer | Non | Point de départ de la numérotation (défaut: 1) |

**Réponse (Initialisation) :**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_images": 24,
  "status": "pending"
}
```

---

#### `GET /api/progress/{job_id}`
Ouvre un flux unidirectionnel permanent (**SSE**) pour suivre le traitement image par image.

**Événements envoyés :**
1. **`image_processed`** :
   ```json
   {
     "type": "image_processed",
     "filename": "original_name.jpg",
     "new_filename": "prefix-1.webp",
     "status": "success",
     "size_before": 1024000,
     "size_after": 256000
   }
   ```
2. **`done`** : Envoyé lorsque toutes les images du job sont traitées.

---

#### `GET /api/job/{job_id}`
Récupère le bilan consolidé après le signal `done`.
- **Réponse :** `200 OK`
- **Body :**
  ```json
  {
    "job_id": "...",
    "status": "completed",
    "stats": {
      "total_before": 25480000,
      "total_after": 4500000,
      "reduction_percent": 82.3,
      "successful": 24,
      "errors": 0
    }
  }
  ```

---

#### `GET /api/download/{job_id}`
Génère le flux de téléchargement final.
- **Comportement :** 
  - Si l'optimisation concernait un fichier unique : Renvoie l'image optimisée.
  - Si plusieurs fichiers : Génère et renvoie dynamiquement un fichier **ZIP** contenant tout le lot renommé.

---

## 🛡️ Gestion des Erreurs et Codes HTTP

| Code | Signification | Cause possible |
| :--- | :--- | :--- |
| `400` | Bad Request | Format non supporté, qualité hors plage (1-100), ou préfixe manquant. |
| `404` | Not Found | Le `job_id` n'existe pas ou a été purgé du serveur (auto-clean > 24h). |
| `413` | Payload Too Large | La taille totale des images dépasse la limite configurée du serveur. |
| `422` | Validation Error | Type de données incorrect dans l'un des champs Form-Data. |

---

## 💻 Exemple d'Intégration (Python Requests)

```python
import requests

url = "http://localhost:8000/api/optimize"
payload = {
    'format': 'webp',
    'quality': '82',
    'prefix': 'voyage-islande',
    'start_number': '1'
}
files = [
    ('files', open('img1.jpg', 'rb')),
    ('files', open('img2.png', 'rb'))
]

response = requests.post(url, data=payload, files=files)
job_id = response.json()['job_id']
print(f"Job démarré : {job_id}")
```

---

## ⚖️ License
Usage interne autorisé sous réserve du respect des droits d'utilisation des bibliothèques logicielles tierces (Pillow, FastAPI).

*Document mis à jour le 23 Mars 2026.* 
Maurice CODJO | Développeur fullstack | Passionné d'IA.
