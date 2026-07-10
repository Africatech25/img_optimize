# API — img_optimize

Documentation de référence de l'API d'optimisation d'images.

**Version** : 2.0.0  
**Base URL** : `https://img-optimize-production.up.railway.app` (production) | `http://localhost:8000` (dev)  
**Stack** : FastAPI 0.115.0 + Uvicorn 0.32.0 + Pillow 11.0.0

---

## Table des matières

1. [Endpoints de diagnostic](#endpoints-de-diagnostic)
2. [Pipeline d'optimisation](#pipeline-doptimisation)
3. [Téléchargement et nettoyage](#téléchargement-et-nettoyage)
4. [Codes HTTP et gestion d'erreurs](#codes-http-et-gestion-derreurs)
5. [Limites de sécurité](#limites-de-sécurité)
6. [Watermarking](#watermarking)
7. [Exemples d'intégration](#exemples-dintégration)

---

## Endpoints de diagnostic

### `GET /api/health`

Vérifie l'état de santé du service et la disponibilité des codecs.

**Réponse** : `200 OK`

```json
{
  "status": "ok",
  "avif_available": true,
  "formats": ["jpeg", "webp", "avif", "png"]
}
```

**Exemple cURL** :
```bash
curl -X GET https://img-optimize-production.up.railway.app/api/health
```

---

### `GET /api/formats`

Récupère les métadonnées et plages de configuration pour chaque format supporté.

**Réponse** : `200 OK`

```json
{
  "webp": {
    "description": "WebP — ultra-efficace, -50% vs JPEG, 97% navigateurs ⭐",
    "default_quality": 70,
    "quality_range": [1, 100],
    "available": true
  },
  "avif": {
    "description": "AVIF — incroyable compression -50-70%, qualite excellente, 90% navigateurs",
    "default_quality": 65,
    "quality_range": [1, 100],
    "available": true
  },
  "jpeg": {
    "description": "JPEG progressif — compression aggresive (reduction -50%), bon rendu",
    "default_quality": 65,
    "quality_range": [1, 95],
    "available": true
  },
  "png": {
    "description": "PNG — compression maximale (niveau 7/9), sans perte",
    "default_quality": 7,
    "quality_range": [1, 9],
    "available": true
  }
}
```

---

## Pipeline d'optimisation

### `POST /api/optimize`

Démarre un job d'optimisation asynchrone et retourne un `job_id` pour suivre la progression via SSE.

**Paramètres** (multipart/form-data) :

| Champ | Type | Obligatoire | Défaut | Contraintes | Description |
|---|---|---|---|---|---|
| `files` | binary[] | Oui | - | Max 200 fichiers, 50 MB/fichier | Images à optimiser |
| `format` | string | Non | `"webp"` | `jpeg\|webp\|avif\|png` | Format de sortie |
| `quality` | integer | Non | Selon format | Voir `/api/formats` | Qualité de compression |
| `prefix` | string | Non | `"image"` | 1-100 caractères | Préfixe des fichiers optimisés |
| `start_number` | integer | Non | `1` | >= 1 | Numéro de départ de la numérotation |
| `smoothing` | integer | Non | `0` | 0-10 | Intensité du lissage (0 = aucun) |
| `watermark_enabled` | string | Non | `"false"` | `true\|false` | Activer le watermarking |
| `watermark_type` | string | Non | `"text"` | `text\|image` | Type de watermark |
| `watermark_text` | string | Non | `""` | Max 200 caractères | Texte du watermark |
| `watermark_logo` | binary | Non | - | Max 50 MB | Logo pour watermark image |
| `watermark_position` | string | Non | `"bottom-right"` | Voir [Watermarking](#watermarking) | Position du watermark |
| `watermark_opacity` | string | Non | `"50"` | 0-100 | Opacité du watermark |

**Réponse** : `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_images": 24,
  "status": "pending"
}
```

**Codes d'erreur** :

| Code | Signification | Cause |
|---|---|---|
| `400` | Bad Request | Format non supporté, qualité hors plage, logo invalide, nombre de fichiers > 100 |
| `413` | Payload Too Large | Fichier > 50 MB |
| `422` | Validation Error | Type de données incorrect dans Form-Data |

**Exemple cURL** :
```bash
curl -X POST https://img-optimize-production.up.railway.app/api/optimize \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.png" \
  -F "format=webp" \
  -F "quality=80" \
  -F "prefix=produit-chaussures" \
  -F "start_number=1"
```

**Exemple Python** :
```python
import requests

url = "https://img-optimize-production.up.railway.app/api/optimize"
files = [
    ('files', open('photo1.jpg', 'rb')),
    ('files', open('photo2.png', 'rb'))
]
data = {
    'format': 'webp',
    'quality': 80,
    'prefix': 'produit-chaussures',
    'start_number': 1
}

response = requests.post(url, files=files, data=data)
job_id = response.json()['job_id']
print(f"Job ID: {job_id}")
```

---

### `GET /api/progress/{job_id}`

Ouvre un flux **Server-Sent Events (SSE)** pour suivre la progression en temps réel.

**Paramètres** :
- `job_id` (path) : UUID du job

**Stream SSE** : `text/event-stream`

**Événements envoyés** :

1. **`started`** :
```json
{
  "type": "started",
  "message": "Démarrage de l'optimisation de 24 image(s)...",
  "timestamp": "2026-04-03T17:45:00.123Z"
}
```

2. **`batch_started`** (si > 10 images) :
```json
{
  "type": "batch_started",
  "message": "Traitement du lot 2/3 (10 image(s))...",
  "timestamp": "2026-04-03T17:45:05.456Z"
}
```

3. **`image_processed`** :
```json
{
  "type": "image_processed",
  "original_name": "photo1.jpg",
  "optimized_name": "produit-chaussures-01.webp",
  "before": 1024000,
  "after": 256000,
  "gain_percent": 75.0,
  "before_formatted": "1.00 MB",
  "after_formatted": "250.00 KB",
  "success": true,
  "index": 1,
  "timestamp": "2026-04-03T17:45:06.789Z"
}
```

4. **`image_error`** :
```json
{
  "type": "image_error",
  "original_name": "corrupted.jpg",
  "error": "[PIL.UnidentifiedImageError] cannot identify image file",
  "success": false,
  "index": 5,
  "timestamp": "2026-04-03T17:45:10.123Z"
}
```

5. **`completed`** :
```json
{
  "type": "completed",
  "message": "Optimisation terminée ! 23/24 images traitées",
  "timestamp": "2026-04-03T17:46:00.000Z",
  "stats": {
    "total_before": 25480000,
    "total_after": 4500000,
    "successful": 23,
    "errors": 1,
    "reduction_percent": 82.3
  }
}
```

6. **`done`** (signal de fin) :
```json
{
  "type": "done",
  "status": "completed"
}
```

**Codes d'erreur** :
- `404` : Job non trouvé

**Exemple JavaScript** :
```javascript
const eventSource = new EventSource(
  `https://img-optimize-production.up.railway.app/api/progress/${jobId}`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'image_processed') {
    console.log(`✓ ${data.optimized_name} - Gain: ${data.gain_percent}%`);
  }
  
  if (data.type === 'done') {
    eventSource.close();
    console.log('Optimisation terminée');
  }
};
```

---

### `GET /api/job/{job_id}`

Récupère le bilan consolidé d'un job (après complétion ou en cours).

**Paramètres** :
- `job_id` (path) : UUID du job

**Réponse** : `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total_images": 24,
  "processed_images": 24,
  "stats": {
    "total_before": 25480000,
    "total_after": 4500000,
    "successful": 23,
    "errors": 1,
    "reduction_percent": 82.3
  }
}
```

**Codes d'erreur** :
- `404` : Job non trouvé

---

## Téléchargement et nettoyage

### `GET /api/download/{job_id}`

Télécharge les images optimisées.

**Comportement** :
- **1 seule image** : télécharge directement le fichier
- **Plusieurs images** : télécharge un ZIP

**Paramètres** :
- `job_id` (path) : UUID du job

**Réponse** :
- `200 OK` : `application/octet-stream` (fichier unique) ou `application/zip` (multiple)
- `400` : Job pas encore terminé
- `404` : Job non trouvé ou aucun fichier optimisé

**Exemple cURL** :
```bash
curl -X GET https://img-optimize-production.up.railway.app/api/download/${JOB_ID} \
  -o optimized-images.zip
```

---

### `GET /api/download/{job_id}/{filename}`

Télécharge une seule image optimisée spécifique.

**Paramètres** :
- `job_id` (path) : UUID du job
- `filename` (path) : Nom du fichier (ex: `produit-chaussures-01.webp`)

**Réponse** :
- `200 OK` : `application/octet-stream`
- `404` : Job ou fichier non trouvé

---

### `GET /api/download-zip/{job_id}`

Force le téléchargement en ZIP (même pour une seule image).

**Paramètres** :
- `job_id` (path) : UUID du job

**Réponse** :
- `200 OK` : `application/zip`
- `400` : Job pas encore terminé
- `404` : Job non trouvé

---

### `DELETE /api/cleanup/{job_id}`

Nettoie les fichiers temporaires d'un job et le retire de la mémoire.

**Paramètres** :
- `job_id` (path) : UUID du job

**Réponse** : `200 OK`

```json
{
  "status": "cleaned"
}
```

**Codes d'erreur** :
- `404` : Job non trouvé

---

## Codes HTTP et gestion d'erreurs

| Code | Signification | Endpoints concernés | Exemples de causes |
|---|---|---|---|
| `200` | OK | Tous (GET/POST/DELETE) | Succès |
| `400` | Bad Request | `/api/optimize` | Format non supporté, qualité hors plage, nombre de fichiers > 100, logo invalide, watermark_opacity hors 0-100, smoothing hors 0-10 |
| `404` | Not Found | `/api/progress`, `/api/job`, `/api/download*`, `/api/cleanup` | Job non trouvé (purgé après 24h ou jamais créé), fichier non trouvé |
| `413` | Payload Too Large | `/api/optimize` | Fichier > 50 MB (MAX_FILE_SIZE) |
| `422` | Unprocessable Entity | `/api/optimize` | Type de données incorrect dans Form-Data (ex: `quality` non entier) |

**Format de réponse d'erreur** (FastAPI standard) :
```json
{
  "detail": "Message explicite de l'erreur"
}
```

---

## Limites de sécurité

Configurées dans `backend/main.py` :

| Limite | Valeur | Justification |
|---|---|---|
| `MAX_FILE_SIZE` | 50 MB | Prévention DoS par upload massif |
| `MAX_FILES_PER_REQUEST` | 200 fichiers | Limite mémoire serveur |
| `ALLOWED_ORIGINS` (CORS) | Liste blanche | Sécurité production (pas de wildcard) |
| Auto-cleanup jobs | 24 heures | Jobs `completed` ou `error` supprimés automatiquement |
| Extensions supportées | `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.tif` | Validation MIME côté serveur |

**CORS origins autorisées** :
- `https://img-optimize.vercel.app` (production frontend)
- `http://localhost:5173` (dev Vite)
- `http://localhost:3000` (dev alternative)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

---

## Watermarking

Fonctionnalité de marquage des images pour protection et branding.

### Types de watermark

#### 1. Watermark texte

**Paramètres** :
```
watermark_enabled=true
watermark_type=text
watermark_text="© 2026 Mon Entreprise"
watermark_position=bottom-right
watermark_opacity=50
```

#### 2. Watermark image (logo)

**Paramètres** :
```
watermark_enabled=true
watermark_type=image
watermark_logo=@logo.png
watermark_position=center
watermark_opacity=30
```

### Positions supportées

| Position | Description |
|---|---|
| `top-left` | Coin supérieur gauche |
| `top-center` | Centre supérieur |
| `top-right` | Coin supérieur droit |
| `center-left` | Centre gauche |
| `center` | Centre absolu |
| `center-right` | Centre droit |
| `bottom-left` | Coin inférieur gauche |
| `bottom-center` | Centre inférieur |
| `bottom-right` | Coin inférieur droit (défaut) |

### Contraintes

- **Opacité** : 0-100 (0 = transparent, 100 = opaque)
- **Taille logo** : Max 50 MB
- **Formats logo** : Mêmes que les images (`.jpg`, `.png`, etc.)
- **Position** : Calculée automatiquement avec marges (10% de l'image)

### Exemple complet

```bash
curl -X POST https://img-optimize-production.up.railway.app/api/optimize \
  -F "files=@photo1.jpg" \
  -F "format=webp" \
  -F "quality=80" \
  -F "prefix=branding" \
  -F "watermark_enabled=true" \
  -F "watermark_type=image" \
  -F "watermark_logo=@logo.png" \
  -F "watermark_position=bottom-right" \
  -F "watermark_opacity=40"
```

---

## Exemples d'intégration

### Workflow complet (Python)

```python
import requests
import time

BASE_URL = "https://img-optimize-production.up.railway.app"

# 1. Démarrer l'optimisation
files = [('files', open(f'photo{i}.jpg', 'rb')) for i in range(1, 25)]
data = {
    'format': 'webp',
    'quality': 75,
    'prefix': 'ecommerce-produit',
    'watermark_enabled': 'true',
    'watermark_type': 'text',
    'watermark_text': '© 2026 Ma Boutique',
    'watermark_opacity': '50'
}

response = requests.post(f"{BASE_URL}/api/optimize", files=files, data=data)
job_id = response.json()['job_id']
print(f"Job démarré: {job_id}")

# 2. Suivre la progression (SSE en Python nécessite sseclient-py)
# Ou polling simple :
while True:
    status_response = requests.get(f"{BASE_URL}/api/job/{job_id}")
    job = status_response.json()
    
    print(f"Progression: {job['processed_images']}/{job['total_images']}")
    
    if job['status'] == 'completed':
        print(f"✓ Terminé! Réduction: {job['stats']['reduction_percent']}%")
        break
    
    time.sleep(2)

# 3. Télécharger les résultats
download_response = requests.get(f"{BASE_URL}/api/download/{job_id}")
with open('optimized-images.zip', 'wb') as f:
    f.write(download_response.content)

# 4. Nettoyer
requests.delete(f"{BASE_URL}/api/cleanup/{job_id}")
```

### Frontend React (SSE)

```javascript
const optimizeImages = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('format', 'webp');
  formData.append('quality', '80');
  formData.append('prefix', 'upload');

  // Démarrer le job
  const response = await fetch(`${BASE_URL}/api/optimize`, {
    method: 'POST',
    body: formData
  });
  
  const { job_id } = await response.json();

  // Suivre la progression
  const eventSource = new EventSource(`${BASE_URL}/api/progress/${job_id}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'image_processed') {
      updateProgress(data.optimized_name, data.gain_percent);
    }
    
    if (data.type === 'done') {
      eventSource.close();
      downloadResults(job_id);
    }
  };
};
```

---

## Réparation de PDF

Fonctionnalité de validation et de réparation de fichiers PDF corrompus.

### `POST /api/pdf/validate`

Valide la structure interne d'un PDF et retourne les informations détaillées.

**Paramètres** (multipart/form-data) :
- `file` (binary, obligatoire) : Fichier PDF à valider (max 50 MB)

**Réponse** : `200 OK`

```json
{
  "validation": {
    "is_valid": false,
    "is_corrupted": true,
    "pages": 5,
    "size_bytes": 2048576,
    "errors": ["Erreur PDF détectée: xref table corrompue"],
    "warnings": ["PDF corrompu mais récupérable avec allow_recovery=True"]
  },
  "info": {
    "pages": 5,
    "title": "Mon Document",
    "author": "John Doe",
    "subject": "Test",
    "producer": "Adobe Acrobat",
    "creation_date": "2026-04-01T10:30:00",
    "encryption": false,
    "size_bytes": 2048576,
    "error": null
  }
}
```

**Codes d'erreur** :
- `400` : PDF invalide ou impossible à valider
- `413` : Fichier trop volumineux (max 50 MB)
- `422` : Type de fichier incorrect (non application/pdf)
- `500` : Erreur serveur

**Exemple cURL** :
```bash
curl -X POST https://img-optimize-production.up.railway.app/api/pdf/validate \
  -F "file=@document.pdf"
```

---

### `POST /api/pdf/repair`

Répare un fichier PDF corrompu en reconstituant la xref table et en supprimant les objets corrompus.

**Paramètres** (multipart/form-data) :
- `file` (binary, obligatoire) : Fichier PDF à réparer (max 50 MB)

**Réponse** : `200 OK`
- Le fichier PDF réparé est retourné en téléchargement direct

**Codes d'erreur** :
- `400` : PDF impossible à réparer
- `413` : Fichier trop volumineux (max 50 MB)
- `422` : Type de fichier incorrect (non application/pdf)
- `500` : Erreur serveur

**Exemple cURL** :
```bash
curl -X POST https://img-optimize-production.up.railway.app/api/pdf/repair \
  -F "file=@document-corrupted.pdf" \
  -o document-repaired.pdf
```

**Exemple JavaScript** :
```javascript
const repairPDF = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    `${BASE_URL}/api/pdf/repair`,
    {
      method: 'POST',
      body: formData
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    console.error('Réparation échouée:', error.detail);
    return;
  }
  
  // Télécharger le PDF réparé
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'document-repaired.pdf';
  link.click();
};
```

---

### `POST /api/pdf/info`

Récupère les métadonnées d'un PDF sans le valider complètement.

**Paramètres** (multipart/form-data) :
- `file` (binary, obligatoire) : Fichier PDF (max 50 MB)

**Réponse** : `200 OK`

```json
{
  "pages": 5,
  "title": "Mon Document",
  "author": "John Doe",
  "subject": "Test",
  "producer": "Adobe Acrobat",
  "creation_date": "2026-04-01T10:30:00",
  "encryption": false,
  "size_bytes": 2048576,
  "error": null
}
```

**Codes d'erreur** :
- `413` : Fichier trop volumineux (max 50 MB)
- `422` : Type de fichier incorrect (non application/pdf)
- `500` : Erreur serveur

**Exemple cURL** :
```bash
curl -X POST https://img-optimize-production.up.railway.app/api/pdf/info \
  -F "file=@document.pdf"
```

---

### Workflow de réparation recommandé

1. **Valider** le PDF avec `/api/pdf/validate`
2. **Examiner** les erreurs et avertissements
3. **Réparer** avec `/api/pdf/repair` si réparable
4. **Vérifier** le PDF réparé en relançant la validation

**Exemple complet (Python)** :

```python
import requests

BASE_URL = "https://img-optimize-production.up.railway.app"

# 1. Valider
with open('document.pdf', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/api/pdf/validate",
        files={'file': f}
    )

validation = response.json()
print(f"Valide: {validation['validation']['is_valid']}")
print(f"Corrompu: {validation['validation']['is_corrupted']}")

if not validation['validation']['is_valid']:
    print("Erreurs détectées:")
    for err in validation['validation']['errors']:
        print(f"  - {err}")

# 2. Réparer si corrompu
if validation['validation']['is_corrupted']:
    with open('document.pdf', 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/api/pdf/repair",
            files={'file': f}
        )
    
    if response.status_code == 200:
        with open('document-repaired.pdf', 'wb') as f:
            f.write(response.content)
        print("✓ PDF réparé et téléchargé")
    else:
        error = response.json()
        print(f"✗ Réparation échouée: {error['detail']}")
```

---

## Convention d'erreurs

Toutes les erreurs sont retournées au format JSON FastAPI standard :

```json
{
  "detail": "Message explicite de l'erreur"
}
```

**Exemples** :
```json
{
  "detail": "Format non supporté: gif"
}
```

```json
{
  "detail": "Fichier 'image_énorme.jpg' trop volumineux (max 50MB)"
}
```

```json
{
  "detail": "Maximum 200 fichiers autorisés (reçu: 250)"
}
```

---

## Notes techniques

- **Traitement asynchrone** : Les images sont traitées en arrière-plan par lots de 10 si > 10 fichiers
- **Persistence** : Jobs stockés en mémoire (dictionnaire Python), pas de base de données
- **Cleanup automatique** : Tâche background exécutée toutes les heures pour supprimer les jobs > 24h
- **Limite de taille par image** : 1 MB après optimisation (ajustement automatique de la qualité si dépassement)
- **SSE buffering** : Headers `Cache-Control: no-cache`, `X-Accel-Buffering: no` pour éviter le buffering proxy
- **Formats optimisés** : WebP (méthode 6), JPEG (progressif), AVIF (si disponible), PNG (niveau 7/9)

---

**Dernière mise à jour** : 2026-04-03  
**Mainteneur** : Maurice CODJO  
**Source** : [GitHub - img_optimize](https://github.com/votre-repo/img_optimize)
