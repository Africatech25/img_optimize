# ImgOpt - Frontend

Interface utilisateur pour l'optimisation d'images et videos.

## Stack
- React 18
- Vite 6
- Tailwind CSS 3
- React Router DOM
- Lucide React (icones)
- Vercel Analytics

## Developpement

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Le build est genere dans `dist/` (~230 KB gzip).

## Variables d'environnement

| Variable | Description |
| :--- | :--- |
| `VITE_API_URL` | URL du backend API (defaut : relatif) |

## Structure

```
src/
  components/     # Composants UI reutilisables
    DropZone.jsx      # Zone de depot fichiers
    ImageGrid.jsx     # Grille d'apercu fichiers
    ParamsPanel.jsx   # Panneau de parametres
    ProgressLog.jsx   # Log de progression SSE
    ResultCard.jsx    # Carte de resultat
    Navbar.jsx        # Barre de navigation
  pages/
    Landing.jsx       # Page d'accueil
    Optimizer.jsx     # Page principale d'optimisation
    Security.jsx      # Page securite
  App.jsx
  main.jsx
```
