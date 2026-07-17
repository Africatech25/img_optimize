# Système d'avis utilisateurs — Design

Date : 2026-07-17

## Contexte

La Landing page (`frontend/src/pages/Landing.jsx`) affiche actuellement une section
"Testimonials" alimentée par un tableau statique codé en dur (`TESTIMONIALS`). Le but
est de remplacer cette source statique par de vrais avis soumis par les utilisateurs
de la plateforme, avec une modération admin avant publication.

## Décisions (issues du brainstorming)

- **Accès** : seuls les utilisateurs connectés (JWT) peuvent soumettre un avis.
- **Modération** : chaque avis passe par un statut `pending` et doit être approuvé par
  un admin avant d'apparaître publiquement.
- **Emplacement de soumission** : une page dédiée `/avis`.
- **Format** : note (1-5 étoiles) + texte.
- **Cardinalité** : un seul avis par utilisateur ; le soumettre à nouveau met à jour
  l'avis existant (upsert) et le repasse en `pending`.
- **Landing page** : la section Testimonials va chercher les avis publics approuvés
  via l'API, avec repli sur le tableau statique actuel si la liste est vide (pour ne
  jamais afficher une section creuse, ex. juste après le déploiement).

## Backend (`backend_django`)

### Nouvelle app `reviews`

Suit le pattern des apps existantes (`optimizer`, `dashboard`, `accounts`).

**Modèle `Review`** (`reviews/models.py`) :

| Champ | Type | Notes |
|---|---|---|
| `user` | `OneToOneField(accounts.User, on_delete=CASCADE)` | 1 avis par utilisateur |
| `rating` | `IntegerField` | validé 1-5 (`MinValueValidator`/`MaxValueValidator`) |
| `text` | `TextField` | max 500 caractères |
| `status` | `CharField` choices `pending`/`approved`/`rejected` | défaut `pending` |
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `updated_at` | `DateTimeField(auto_now=True)` | |

**Endpoints publics/utilisateur** (`reviews/urls.py`, monté sur `/api/reviews/`) :

- `GET /api/reviews/public` — liste paginée des avis `status=approved`, triés par
  `created_at` décroissant. Pas d'auth requise. Champs retournés : nom affiché
  (`display_name` de l'utilisateur, ou email tronqué avant `@` si `display_name` est
  vide), `rating`, `text`, `created_at`.
- `GET /api/reviews/me` — avis de l'utilisateur connecté (404 si aucun). Auth JWT requise.
- `PUT /api/reviews/me` — crée ou met à jour l'avis de l'utilisateur connecté
  (upsert sur le `OneToOneField`). Remet `status=pending` à chaque écriture. Auth
  JWT requise. Body : `{ "rating": int, "text": str }`.

**Endpoints admin** (ajoutés à `dashboard/api_urls.py`, réutilisent le pattern
`RequireStaff` déjà utilisé par `AdminUserListCreateView`) :

- `GET /api/admin/reviews` — liste tous les avis (tous statuts), avec filtre optionnel
  `?status=pending`.
- `PATCH /api/admin/reviews/<id>` — met à jour le `status` (`approved`/`rejected`).
- `DELETE /api/admin/reviews/<id>` — supprime un avis.

### Registration

- `reviews` ajouté à `INSTALLED_APPS` dans `config/settings.py`.
- `path('api/reviews/', include('reviews.urls'))` ajouté à `config/urls.py`.
- Migration Django standard pour le nouveau modèle.
- Admin Django : `Review` enregistré dans `reviews/admin.py` pour modération de secours
  via `/admin/` (cohérent avec le reste du projet qui expose l'admin Django natif).

## Frontend (`frontend/src`)

### Nouvelle page `/avis` (`pages/Reviews.jsx`)

- Liste des avis publics approuvés : étoiles, texte, nom affiché — récupérés via
  `GET /api/reviews/public` (fetch avec `API_BASE`, pattern identique à
  `useOptimizationJob.js`).
- Formulaire en haut de page :
  - Si connecté (`useAuth()`/`isAuthenticated`) : formulaire note (sélecteur 1-5
    étoiles) + textarea, pré-rempli via `GET /api/reviews/me` si un avis existe déjà.
    Soumission → `PUT /api/reviews/me`. Message de confirmation indiquant que l'avis
    est en attente de modération.
  - Si non connecté : bandeau CTA vers `/login` (avec `state: { from: '/avis' }`,
    pattern déjà utilisé dans `Account.jsx`).
- Route ajoutée dans `App.jsx` : `<Route path="/avis" element={<Reviews />} />`.

### Landing page (`pages/Landing.jsx`)

- La section Testimonials (ligne ~384) fetch `GET /api/reviews/public` au montage.
- Si la réponse contient au moins un avis → affiche les avis réels (mappés sur la
  même structure d'affichage que l'actuel `TESTIMONIALS.map`).
- Si la liste est vide (erreur réseau ou aucun avis approuvé) → repli sur le tableau
  `TESTIMONIALS` statique existant, conservé dans le code comme fallback.
- Lien "Avis" ajouté dans le footer, section "Produit" (à côté de "Témoignages" /
  "Sécurité").

### Navbar

- Lien "Avis" ajouté à la navigation publique (`components/Navbar.jsx`), pointant
  vers `/avis`.

### Admin (`pages/admin/`)

- Nouvelle page `AdminReviews.jsx`, suit le pattern de `AdminJobs.jsx`/`AdminUsers.jsx` :
  tableau des avis avec filtre par statut, actions "Approuver" / "Rejeter" / "Supprimer".
- Route ajoutée sous `/admin` dans `App.jsx` : `<Route path="reviews" element={<AdminReviews />} />`.
- Lien ajouté à la nav d'`AdminLayout.jsx`.

## Hors périmètre (YAGNI)

- Pas de réponse admin aux avis (pas de champ "réponse officielle").
- Pas de système de vote "utile"/"pas utile" sur les avis.
- Pas de notification email lors de l'approbation/rejet.
- Pas de limite de taux (rate limiting) spécifique sur `PUT /api/reviews/me` au-delà
  des throttles DRF déjà configurés globalement — un avis par utilisateur limite déjà
  fortement l'abus.
