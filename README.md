# 🖼️ Image Optimizer - Web App

Application web moderne pour optimiser vos images pour le web. Interface intuitive avec drag & drop + API REST complète.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-teal)

## ✨ Fonctionnalités

- 🎨 **Interface moderne** avec design responsive dark mode
- 📤 **Drag & Drop** pour upload rapide d'images
- 🔄 **4 formats supportés** : JPEG, WebP, AVIF, PNG
- ⚙️ **Qualité réglable** selon le format choisi
- 🏷️ **Renommage automatique** avec préfixe personnalisable
- 📊 **Statistiques détaillées** (taille avant/après, réduction %)
- 📦 **Téléchargement en ZIP** de toutes les images optimisées
- 🚫 **Suppression EXIF** pour protéger la vie privée
- 🌐 **API REST complète** pour intégration dans vos apps

## 📸 Formats supportés

| Format | Description | Réduction | Compatibilité |
|--------|-------------|-----------|---------------|
| **WebP** ⭐ | Recommandé - 30-50% plus léger que JPEG | Excellente | 97% navigateurs |
| **AVIF** | Ultra-léger, qualité supérieure | Exceptionnelle | ~90% navigateurs |
| **JPEG** | Maximum compatibilité, progressif | Bonne | 100% navigateurs |
| **PNG** | Sans perte, idéal pour logos/transparence | Modérée | 100% navigateurs |

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation rapide

```bash
# 1. Cloner ou télécharger le projet
cd img_optimize

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer le serveur
python main.py
```

L'application sera accessible sur : **http://localhost:8000**

## 📖 Utilisation

### Interface Web

1. Ouvrez votre navigateur sur `http://localhost:8000`
2. Glissez-déposez vos images ou cliquez pour les sélectionner
3. Choisissez le format de sortie (WebP recommandé)
4. Ajustez la qualité si nécessaire
5. Définissez un préfixe pour le renommage
6. Cliquez sur "Optimiser les images"
7. Téléchargez vos images individuellement ou en ZIP

### API REST

#### Optimiser des images

```bash
POST /api/optimize
Content-Type: multipart/form-data

Parameters:
- files: List[File] (images à optimiser)
- format: str (jpeg|webp|avif|png) - défaut: webp
- quality: int - défaut: auto selon format
- prefix: str - préfixe de renommage
```

**Exemple avec cURL:**

```bash
curl -X POST http://localhost:8000/api/optimize \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "format=webp" \
  -F "quality=85" \
  -F "prefix=vacances-2026"
```

**Réponse:**

```json
{
  "session_id": "abc-123-def",
  "total_images": 2,
  "successful": 2,
  "results": [
    {
      "original_name": "photo1.jpg",
      "optimized_name": "vacances-2026-01.webp",
      "download_url": "/api/download/abc-123-def/vacances-2026-01.webp",
      "original_size": 2500000,
      "optimized_size": 850000,
      "reduction_percent": 66.0,
      "dimensions": {"width": 1920, "height": 1080}
    }
  ],
  "download_all_url": "/api/download-all/abc-123-def"
}
```

#### Télécharger une image optimisée

```bash
GET /api/download/{session_id}/{filename}
```

#### Télécharger toutes les images en ZIP

```bash
GET /api/download-all/{session_id}
```

#### Obtenir les formats disponibles

```bash
GET /api/formats
```

**Réponse:**

```json
{
  "webp": {
    "description": "WebP — 30-50% plus léger que JPEG",
    "default_quality": 82,
    "quality_range": [1, 100]
  }
}
```

## 🎯 Exemples d'utilisation

### Optimiser pour un site web

```bash
# Photos produits en WebP qualité 85
python -c "
import requests

files = [
    ('files', open('produit1.jpg', 'rb')),
    ('files', open('produit2.jpg', 'rb'))
]

response = requests.post('http://localhost:8000/api/optimize',
    files=files,
    data={'format': 'webp', 'quality': 85, 'prefix': 'produit'}
)

print(response.json())
"
```

### Intégration dans une app Python

```python
import requests

def optimize_images(image_paths, output_format='webp', quality=82):
    files = [('files', open(path, 'rb')) for path in image_paths]

    response = requests.post(
        'http://localhost:8000/api/optimize',
        files=files,
        data={
            'format': output_format,
            'quality': quality,
            'prefix': 'optimized'
        }
    )

    return response.json()

# Utilisation
result = optimize_images(['photo1.jpg', 'photo2.png'], format='webp')
print(f"Optimisé: {result['successful']}/{result['total_images']}")
```

## 📁 Structure du projet

```
img_optimize/
├── main.py                 # API FastAPI
├── optimize_images.py      # Script CLI original
├── requirements.txt        # Dépendances Python
├── static/
│   └── index.html         # Interface web
├── temp_uploads/          # Uploads temporaires
└── temp_outputs/          # Fichiers optimisés
```

## ⚙️ Configuration

### Qualité par défaut par format

- **JPEG** : 82 (1-95)
- **WebP** : 82 (1-100)
- **AVIF** : 80 (1-100)
- **PNG** : 6 (1-9, niveau de compression)

### Personnaliser le serveur

```python
# Dans main.py, modifier ces lignes :
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",  # Écouter sur toutes les interfaces
        port=8000,        # Port personnalisé
        reload=True       # Auto-reload en dev
    )
```

## 🔧 Dépannage

### AVIF ne fonctionne pas

```bash
pip install --upgrade Pillow pillow-avif-plugin
```

### Port 8000 déjà utilisé

```bash
# Lancer sur un autre port
python -c "import uvicorn; from main import app; uvicorn.run(app, port=8080)"
```

### Erreur de mémoire avec grandes images

Augmenter la limite dans Pillow :

```python
# Ajouter en haut de main.py
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Désactive la limite
```

## 🚦 Déploiement en production

### Avec Gunicorn (recommandé)

```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Avec Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t image-optimizer .
docker run -p 8000:8000 image-optimizer
```

## 📝 License

MIT License - Libre d'utilisation

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à ouvrir une issue ou un PR.

## 📧 Support

Pour toute question ou problème, ouvrez une issue sur le dépôt.

---

**Développé avec ❤️ et FastAPI**
