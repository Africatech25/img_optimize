# Système d'avis utilisateurs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre aux utilisateurs connectés de laisser un avis (note 1-5 + texte) sur la plateforme, modéré par un admin avant publication, et afficher les avis approuvés sur la Landing page à la place des témoignages statiques actuels.

**Architecture:** Nouvelle app Django `reviews` (modèle `Review`, endpoints publics `/api/reviews/public` et `/api/reviews/me`) ; les endpoints de modération admin (`/api/admin/reviews...`) vivent dans l'app `dashboard` existante, en suivant exactement le pattern déjà utilisé pour `AdminJobListView`/`AdminUserListCreateView`. Côté frontend : une nouvelle page `/avis` (liste + formulaire), une nouvelle page admin `AdminReviews`, et la section Testimonials de la Landing page qui bascule sur les vraies données avec repli sur le tableau statique existant.

**Tech Stack:** Django 6 / Django REST Framework / SimpleJWT (backend_django), React 18 + React Router + Tailwind (frontend). Aucune nouvelle dépendance.

## Global Constraints

- Un avis par utilisateur (`OneToOneField` sur `Review.user`), upsert via `PUT /api/reviews/me`.
- Toute écriture (création ou modification) remet `status` à `pending`.
- `GET /api/reviews/public` ne renvoie que les avis `status=approved`, sans authentification requise.
- Endpoints admin protégés par `IsAdminUser` (même pattern que `dashboard/api_views.py`).
- `rating` validé entre 1 et 5 ; `text` max 500 caractères, nettoyé via `accounts.serializers.clean_free_text`.
- Pas de pagination DRF (aucune app du projet n'en utilise) ; le endpoint public se limite aux 50 avis approuvés les plus récents.
- Style de code, nommage, structure de fichiers : suivre exactement les patterns déjà en place dans `accounts/` et `dashboard/` (backend), et `pages/admin/AdminJobs.jsx`/`AdminUsers.jsx` (frontend).

---

## Task 1: Modèle `Review` + app `reviews`

**Files:**
- Create: `backend_django/reviews/__init__.py`
- Create: `backend_django/reviews/apps.py`
- Create: `backend_django/reviews/models.py`
- Create: `backend_django/reviews/admin.py`
- Create: `backend_django/reviews/tests.py`
- Modify: `backend_django/config/settings.py`
- Test: `backend_django/reviews/tests.py`

**Interfaces:**
- Produces: `reviews.models.Review` avec champs `user` (`OneToOneField(settings.AUTH_USER_MODEL, related_name="review")`), `rating` (`IntegerField`, 1-5), `text` (`TextField`, max 500), `status` (`pending`/`approved`/`rejected`, défaut `pending`), `created_at`, `updated_at`. Ordering par défaut `-created_at`.

- [ ] **Step 1: Créer l'app `reviews`**

```bash
cd backend_django
python manage.py startapp reviews
```

- [ ] **Step 2: Écrire le modèle `Review`**

Remplacer le contenu de `backend_django/reviews/models.py` :

```python
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """Avis utilisateur sur la plateforme (note + texte), soumis à
    modération admin avant apparition publique."""

    STATUS_CHOICES = [
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review",
    )
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.user.email} ({self.rating}/5, {self.status})"
```

- [ ] **Step 3: Enregistrer le modèle dans l'admin Django**

Remplacer le contenu de `backend_django/reviews/admin.py` :

```python
from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "rating", "status", "created_at"]
    list_filter = ["status", "rating"]
    search_fields = ["user__email", "text"]
```

- [ ] **Step 4: Déclarer l'app dans `INSTALLED_APPS`**

Modifier `backend_django/config/settings.py:37-54` :

```python
INSTALLED_APPS = [
    # 'dashboard' avant 'django.contrib.admin' : nécessaire pour que notre
    # template admin/index.html personnalisé (lien vers le dashboard) soit
    # trouvé avant celui par défaut de Django (app_directories cherche dans
    # l'ordre d'INSTALLED_APPS et s'arrête au premier match).
    'dashboard',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'optimizer',
    'accounts',
    'reviews',
]
```

- [ ] **Step 5: Générer et appliquer la migration**

```bash
cd backend_django
python manage.py makemigrations reviews
python manage.py migrate
```
Expected: une migration `reviews/migrations/0001_initial.py` est créée et appliquée sans erreur.

- [ ] **Step 6: Écrire un test modèle basique (validation de la contrainte 1 avis/utilisateur)**

Remplacer le contenu de `backend_django/reviews/tests.py` :

```python
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Review

User = get_user_model()


class ReviewModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="alice@example.com", password="testpass123")

    def test_one_review_per_user(self):
        Review.objects.create(user=self.user, rating=5, text="Super outil")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(user=self.user, rating=3, text="Deuxième avis")

    def test_default_status_is_pending(self):
        review = Review.objects.create(user=self.user, rating=4, text="Très pratique")
        self.assertEqual(review.status, "pending")
```

- [ ] **Step 7: Lancer les tests et vérifier qu'ils passent**

```bash
cd backend_django
python manage.py test reviews
```
Expected: `OK` (2 tests passés).

- [ ] **Step 8: Commit**

```bash
git add backend_django/reviews backend_django/config/settings.py
git commit -m "feat: add Review model and reviews app"
```

---

## Task 2: Endpoints publics `/api/reviews/public` et `/api/reviews/me`

**Files:**
- Create: `backend_django/reviews/serializers.py`
- Create: `backend_django/reviews/views.py`
- Create: `backend_django/reviews/urls.py`
- Modify: `backend_django/config/urls.py`
- Modify: `backend_django/reviews/tests.py`

**Interfaces:**
- Consumes: `reviews.models.Review` (Task 1), `accounts.serializers.clean_free_text` (fonction existante, `backend_django/accounts/serializers.py:25`).
- Produces:
  - `GET /api/reviews/public` → `200`, liste JSON `[{ "display_name": str, "rating": int, "text": str, "created_at": str }]`, avis `approved` uniquement, 50 max, tri `-created_at`.
  - `GET /api/reviews/me` → `200` avec `{ "rating": int, "text": str, "status": str, "created_at": str, "updated_at": str }` si l'utilisateur a un avis, `404` sinon. Auth JWT requise (`401` sinon).
  - `PUT /api/reviews/me` → body `{ "rating": int, "text": str }`, crée ou met à jour l'avis de l'utilisateur connecté, force `status="pending"`, renvoie `200` avec le même format que le GET. `400` si `rating` hors 1-5 ou `text` vide/absent. Auth JWT requise.

- [ ] **Step 1: Écrire les serializers**

Créer `backend_django/reviews/serializers.py` :

```python
from rest_framework import serializers

from accounts.serializers import clean_free_text

from .models import Review


def display_name_for(user):
    return user.display_name or user.email.split("@")[0]


class PublicReviewSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["display_name", "rating", "text", "created_at"]

    def get_display_name(self, obj):
        return display_name_for(obj.user)


class MyReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "text", "status", "created_at", "updated_at"]


class ReviewWriteSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(max_length=500)

    class Meta:
        model = Review
        fields = ["rating", "text"]

    def validate_text(self, value):
        value = clean_free_text(value)
        if not value:
            raise serializers.ValidationError("Le texte de l'avis ne peut pas être vide.")
        return value
```

- [ ] **Step 2: Écrire les vues**

Créer `backend_django/reviews/views.py` :

```python
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review
from .serializers import MyReviewSerializer, PublicReviewSerializer, ReviewWriteSerializer


class PublicReviewListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(status="approved").select_related("user")[:50]


class MyReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            review = request.user.review
        except Review.DoesNotExist:
            raise NotFound("Aucun avis trouvé.")
        return Response(MyReviewSerializer(review).data)

    def put(self, request):
        serializer = ReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review, _ = Review.objects.update_or_create(
            user=request.user,
            defaults={**serializer.validated_data, "status": "pending"},
        )
        return Response(MyReviewSerializer(review).data, status=status.HTTP_200_OK)
```

- [ ] **Step 3: Déclarer les URLs de l'app**

Créer `backend_django/reviews/urls.py` :

```python
from django.urls import path

from . import views

urlpatterns = [
    path("public", views.PublicReviewListView.as_view()),
    path("me", views.MyReviewView.as_view()),
]
```

- [ ] **Step 4: Monter les URLs sur `/api/reviews/`**

Modifier `backend_django/config/urls.py` :

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('optimizer.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/admin/', include('dashboard.api_urls')),
]
```

- [ ] **Step 5: Écrire les tests des endpoints (échouent d'abord car rien n'est branché avant Step 1-4 — ici on les écrit après pour valider tout le flux, exécuter tout de suite après)**

Ajouter à la fin de `backend_django/reviews/tests.py` :

```python
from rest_framework.test import APITestCase


class PublicReviewListViewTests(APITestCase):
    def setUp(self):
        self.approved_user = User.objects.create_user(email="approved@example.com", password="testpass123")
        self.pending_user = User.objects.create_user(email="pending@example.com", password="testpass123")
        Review.objects.create(user=self.approved_user, rating=5, text="Excellent", status="approved")
        Review.objects.create(user=self.pending_user, rating=3, text="En attente", status="pending")

    def test_only_approved_reviews_are_public(self):
        res = self.client.get("/api/reviews/public")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["text"], "Excellent")

    def test_display_name_falls_back_to_email_local_part(self):
        res = self.client.get("/api/reviews/public")
        self.assertEqual(res.data[0]["display_name"], "approved")


class MyReviewViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="bob@example.com", password="testpass123")

    def test_get_requires_authentication(self):
        res = self.client.get("/api/reviews/me")
        self.assertEqual(res.status_code, 401)

    def test_get_returns_404_when_no_review(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/reviews/me")
        self.assertEqual(res.status_code, 404)

    def test_put_creates_review_as_pending(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.put("/api/reviews/me", {"rating": 4, "text": "Très bon outil"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "pending")
        self.assertEqual(Review.objects.get(user=self.user).rating, 4)

    def test_put_updates_existing_review_and_resets_to_pending(self):
        Review.objects.create(user=self.user, rating=2, text="Bof", status="approved")
        self.client.force_authenticate(user=self.user)
        res = self.client.put("/api/reviews/me", {"rating": 5, "text": "Finalement excellent"}, format="json")
        self.assertEqual(res.status_code, 200)
        review = Review.objects.get(user=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.status, "pending")
        self.assertEqual(Review.objects.filter(user=self.user).count(), 1)

    def test_put_rejects_rating_out_of_range(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.put("/api/reviews/me", {"rating": 6, "text": "..."}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_put_rejects_empty_text(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.put("/api/reviews/me", {"rating": 4, "text": "   "}, format="json")
        self.assertEqual(res.status_code, 400)
```

- [ ] **Step 6: Lancer les tests et vérifier qu'ils passent**

```bash
cd backend_django
python manage.py test reviews
```
Expected: `OK` (9 tests passés au total avec ceux de Task 1).

- [ ] **Step 7: Commit**

```bash
git add backend_django/reviews backend_django/config/urls.py
git commit -m "feat: add public review endpoints (list, get/put own review)"
```

---

## Task 3: Endpoints admin de modération

**Files:**
- Modify: `backend_django/dashboard/serializers.py`
- Modify: `backend_django/dashboard/api_views.py`
- Modify: `backend_django/dashboard/api_urls.py`
- Modify: `backend_django/dashboard/tests.py`

**Interfaces:**
- Consumes: `reviews.models.Review` (Task 1).
- Produces:
  - `GET /api/admin/reviews` → liste tous les avis (staff uniquement), filtrable via `?status=pending`.
  - `PATCH /api/admin/reviews/<id>` → met à jour `status` (`approved`/`rejected`) uniquement.
  - `DELETE /api/admin/reviews/<id>` → supprime l'avis.

- [ ] **Step 1: Écrire les tests admin (ils échoueront tant que les vues n'existent pas)**

Remplacer le contenu de `backend_django/dashboard/tests.py` :

```python
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from reviews.models import Review

User = get_user_model()


class AdminReviewListViewTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@example.com", password="testpass123", is_staff=True)
        self.regular = User.objects.create_user(email="regular@example.com", password="testpass123")
        self.reviewer = User.objects.create_user(email="reviewer@example.com", password="testpass123")
        Review.objects.create(user=self.reviewer, rating=5, text="Top", status="pending")

    def test_requires_staff(self):
        self.client.force_authenticate(user=self.regular)
        res = self.client.get("/api/admin/reviews")
        self.assertEqual(res.status_code, 403)

    def test_staff_can_list_all_reviews(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.get("/api/admin/reviews")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["user_email"], "reviewer@example.com")

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.get("/api/admin/reviews?status=approved")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0)


class AdminReviewDetailViewTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff2@example.com", password="testpass123", is_staff=True)
        self.reviewer = User.objects.create_user(email="reviewer2@example.com", password="testpass123")
        self.review = Review.objects.create(user=self.reviewer, rating=4, text="Bien", status="pending")

    def test_patch_approves_review(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(f"/api/admin/reviews/{self.review.id}", {"status": "approved"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, "approved")

    def test_patch_ignores_rating_and_text_changes(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(
            f"/api/admin/reviews/{self.review.id}",
            {"status": "approved", "rating": 1, "text": "Modifié par admin"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.text, "Bien")

    def test_delete_removes_review(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.delete(f"/api/admin/reviews/{self.review.id}")
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())
```

- [ ] **Step 2: Vérifier que les tests échouent (endpoints inexistants)**

```bash
cd backend_django
python manage.py test dashboard
```
Expected: FAIL — `404` au lieu de `403`/`200` sur `/api/admin/reviews` (route non déclarée).

- [ ] **Step 3: Ajouter le serializer admin**

Ajouter à la fin de `backend_django/dashboard/serializers.py` :

```python
from reviews.models import Review


class AdminReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user_email", "display_name", "rating", "text", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "user_email", "display_name", "rating", "text", "created_at", "updated_at"]
```

- [ ] **Step 4: Ajouter les vues admin**

Dans `backend_django/dashboard/api_views.py`, remplacer la ligne d'import existante :

```python
from .serializers import AdminJobDetailSerializer, AdminJobSerializer
```

par :

```python
from reviews.models import Review

from .serializers import AdminJobDetailSerializer, AdminJobSerializer, AdminReviewSerializer
```

Puis ajouter les deux vues suivantes à la fin du fichier :

```python
class AdminReviewListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminReviewSerializer

    def get_queryset(self):
        qs = Review.objects.select_related("user").order_by("-created_at")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AdminReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminReviewSerializer
    queryset = Review.objects.select_related("user")
```

- [ ] **Step 5: Déclarer les routes admin**

Modifier `backend_django/dashboard/api_urls.py` :

```python
from django.urls import path

from accounts.admin_views import AdminUserDetailView, AdminUserListCreateView

from . import api_views

urlpatterns = [
    path("stats", api_views.AdminStatsView.as_view()),
    path("jobs", api_views.AdminJobListView.as_view()),
    path("jobs/<uuid:job_id>", api_views.AdminJobDetailView.as_view()),
    path("users", AdminUserListCreateView.as_view()),
    path("users/<int:pk>", AdminUserDetailView.as_view()),
    path("reviews", api_views.AdminReviewListView.as_view()),
    path("reviews/<int:pk>", api_views.AdminReviewDetailView.as_view()),
]
```

- [ ] **Step 6: Lancer les tests et vérifier qu'ils passent**

```bash
cd backend_django
python manage.py test dashboard reviews
```
Expected: `OK` (15 tests passés au total).

- [ ] **Step 7: Commit**

```bash
git add backend_django/dashboard
git commit -m "feat: add admin review moderation endpoints"
```

---

## Task 4: Page `/avis` (liste publique + formulaire)

**Files:**
- Create: `frontend/src/pages/Reviews.jsx`
- Modify: `frontend/src/App.jsx`

**Interfaces:**
- Consumes: `GET /api/reviews/public` (Task 2, sans auth), `GET /api/reviews/me` et `PUT /api/reviews/me` (Task 2, via `authFetch` de `useAuth()` — `frontend/src/context/AuthContext.jsx:146`), `useAuth()` (`isAuthenticated`, `authFetch`).
- Produces: route `/avis`, composant `Reviews` par défaut.

- [ ] **Step 1: Créer la page `Reviews.jsx`**

Créer `frontend/src/pages/Reviews.jsx` :

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || ''

function StarRating({ value, onChange, readOnly = false }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          disabled={readOnly}
          onClick={() => onChange && onChange(n)}
          className={readOnly ? 'cursor-default' : 'cursor-pointer'}
        >
          <Star
            className={`w-5 h-5 ${n <= value ? 'fill-violet-500 text-violet-500' : 'text-slate-600'}`}
          />
        </button>
      ))}
    </div>
  )
}

function ReviewForm() {
  const { authFetch } = useAuth()
  const [rating, setRating] = useState(0)
  const [text, setText] = useState('')
  const [status, setStatus] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadMine() {
      try {
        const res = await authFetch('/api/reviews/me')
        if (res.status === 404) return
        if (!res.ok) throw new Error('Erreur de chargement')
        const data = await res.json()
        if (!cancelled) {
          setRating(data.rating)
          setText(data.text)
          setStatus(data.status)
        }
      } catch {
        // best effort : formulaire vide si le chargement échoue
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    loadMine()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (rating < 1) {
      setError('Choisissez une note de 1 à 5 étoiles.')
      return
    }
    setIsSaving(true)
    try {
      const res = await authFetch('/api/reviews/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, text }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.text?.[0] || data.rating?.[0] || 'Erreur lors de l\'envoi')
      setStatus(data.status)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <p className="text-slate-400 text-center">Chargement...</p>
  }

  return (
    <form onSubmit={handleSubmit} className="glass-card gradient-border p-8 rounded-[2rem] space-y-4">
      <h2 className="text-xl font-bold text-white">
        {status ? 'Modifier mon avis' : 'Laisser un avis'}
      </h2>
      <StarRating value={rating} onChange={setRating} />
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        maxLength={500}
        rows={4}
        placeholder="Qu'avez-vous pensé de l'outil ?"
        className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
      />
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {status && (
        <p className="text-sm text-slate-400">
          Statut actuel : <span className="font-semibold">{status === 'pending' ? 'en attente de validation' : status === 'approved' ? 'publié' : 'non retenu'}</span>
        </p>
      )}
      <button
        type="submit"
        disabled={isSaving}
        className="px-6 py-2.5 bg-white text-black font-bold rounded-xl hover:scale-105 transition-all disabled:opacity-50"
      >
        {isSaving ? 'Envoi...' : status ? 'Mettre à jour' : 'Envoyer mon avis'}
      </button>
    </form>
  )
}

export default function Reviews() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [reviews, setReviews] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadPublic() {
      try {
        const res = await fetch(`${API_BASE}/api/reviews/public`)
        if (res.ok) setReviews(await res.json())
      } finally {
        setIsLoading(false)
      }
    }
    loadPublic()
  }, [])

  return (
    <div className="min-h-screen bg-[#050505] pt-40 pb-20 px-6">
      <div className="max-w-3xl mx-auto space-y-16">
        <div className="text-center">
          <h1 className="text-4xl lg:text-6xl font-bold text-white mb-4">
            Avis des <span className="text-gradient">utilisateurs</span>
          </h1>
          <p className="text-slate-400">Ce que la communauté pense d'ImgOpt.</p>
        </div>

        {!authLoading && (
          isAuthenticated ? (
            <ReviewForm />
          ) : (
            <div className="glass-card p-8 rounded-[2rem] text-center space-y-4">
              <p className="text-slate-400">Connectez-vous pour laisser votre avis.</p>
              <Link
                to="/login"
                state={{ from: '/avis' }}
                className="inline-block px-6 py-2.5 bg-white text-black font-bold rounded-xl hover:scale-105 transition-all"
              >
                Se connecter
              </Link>
            </div>
          )
        )}

        <div className="space-y-6">
          {isLoading ? (
            <p className="text-slate-400 text-center">Chargement des avis...</p>
          ) : reviews.length === 0 ? (
            <p className="text-slate-400 text-center">Aucun avis publié pour l'instant.</p>
          ) : (
            reviews.map((review, idx) => (
              <div key={idx} className="glass-card p-6 rounded-[1.5rem] border border-white/5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-white font-bold">{review.display_name}</span>
                  <StarRating value={review.rating} readOnly />
                </div>
                <p className="text-slate-400 italic font-light">"{review.text}"</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Ajouter la route dans `App.jsx`**

Modifier `frontend/src/App.jsx` :

```jsx
import Security from './pages/Security'
import Reviews from './pages/Reviews'
```

(ajouter l'import `Reviews` juste après celui de `Security`, ligne `frontend/src/App.jsx:10`), puis ajouter la route juste après `/security` (ligne `frontend/src/App.jsx:49`) :

```jsx
          <Route path="/security" element={<Security />} />
          <Route path="/avis" element={<Reviews />} />
```

- [ ] **Step 3: Vérifier manuellement dans le navigateur**

```bash
cd backend_django && python manage.py runserver
```
Dans un autre terminal :
```bash
cd frontend && npm run dev
```
Ouvrir `http://localhost:5173/avis` : la page doit s'afficher sans erreur console, avec le message "Aucun avis publié pour l'instant." et un bandeau de connexion (utilisateur non connecté). Se connecter, revenir sur `/avis`, soumettre un avis, vérifier le message "en attente de validation".

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Reviews.jsx frontend/src/App.jsx
git commit -m "feat: add /avis page for submitting and browsing reviews"
```

---

## Task 5: Landing page — remplacer les témoignages statiques

**Files:**
- Modify: `frontend/src/pages/Landing.jsx`

**Interfaces:**
- Consumes: `GET /api/reviews/public` (Task 2).

- [ ] **Step 1: Ajouter les imports et le state de fetch**

Modifier `frontend/src/pages/Landing.jsx:1` :

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_URL || ''
```

- [ ] **Step 2: Charger les avis publics au montage du composant**

Modifier `frontend/src/pages/Landing.jsx:98-100` (début de `export default function Landing()`) :

```jsx
export default function Landing() {
  const [liveReviews, setLiveReviews] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function loadReviews() {
      try {
        const res = await fetch(`${API_BASE}/api/reviews/public`)
        if (!res.ok) return
        const data = await res.json()
        if (!cancelled && data.length > 0) setLiveReviews(data)
      } catch {
        // repli silencieux sur les témoignages statiques
      }
    }
    loadReviews()
    return () => { cancelled = true }
  }, [])

  const displayedTestimonials = liveReviews || TESTIMONIALS

  return (
    <div className="min-h-screen bg-[#050505] overflow-hidden">
```

- [ ] **Step 3: Adapter le rendu de la section Testimonials**

Modifier `frontend/src/pages/Landing.jsx:394-416` — remplacer `TESTIMONIALS.map` par `displayedTestimonials.map`, et adapter les champs (les vrais avis n'ont pas d'`avatar`/`role`, juste `display_name`/`rating`/`text`) :

```jsx
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {displayedTestimonials.map((testimonial, idx) => (
              <div key={idx} className="glass-card p-8 rounded-[2rem] border border-white/5 hover:border-violet-500/30 transition-all duration-500 group">
                <div className="flex items-center gap-4 mb-6">
                  {testimonial.avatar ? (
                    <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-white/10 group-hover:border-violet-500/50 transition-colors">
                      <img src={testimonial.avatar} alt={testimonial.name} className="w-full h-full object-cover" />
                    </div>
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-600 to-cyan-600 flex items-center justify-center text-white font-bold">
                      {(testimonial.display_name || '?')[0].toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h4 className="text-white font-bold">{testimonial.name || testimonial.display_name}</h4>
                    {testimonial.role && <p className="text-slate-500 text-sm">{testimonial.role}</p>}
                  </div>
                </div>
                <p className="text-slate-400 italic font-light leading-relaxed">
                  "{testimonial.text}"
                </p>
                <div className="mt-6 flex gap-1 text-violet-500/60">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <i
                      key={s}
                      className={`fa-solid fa-star text-xs ${testimonial.rating && s > testimonial.rating ? 'opacity-30' : ''}`}
                    ></i>
                  ))}
                </div>
              </div>
            ))}
          </div>
```

- [ ] **Step 4: Ajouter le lien "Avis" au footer**

Modifier `frontend/src/pages/Landing.jsx:479` :

```jsx
              { title: 'Produit', links: [{ label: 'Fonctionnalités', href: '/#features' }, { label: 'Témoignages', href: '/#testimonials' }, { label: 'Avis', href: '/avis' }, { label: 'Sécurité', href: '/security' }] },
```

- [ ] **Step 5: Vérifier manuellement dans le navigateur**

Avec les deux serveurs lancés (Task 4, Step 3) : ouvrir `http://localhost:5173/`, vérifier que la section Testimonials affiche encore le tableau statique (aucun avis approuvé en base). Depuis Django admin (`/admin/`) ou `python manage.py shell`, approuver un avis créé au Task 4 (`Review.objects.filter(status="pending").update(status="approved")`), recharger la Landing page : la section doit maintenant afficher l'avis réel.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Landing.jsx
git commit -m "feat: source Landing testimonials from approved reviews with static fallback"
```

---

## Task 6: Navbar — lien "Avis"

**Files:**
- Modify: `frontend/src/components/Navbar.jsx`

**Interfaces:**
- Consumes: aucune nouvelle interface, ajout de contenu statique.

- [ ] **Step 1: Ajouter l'entrée dans `menuLinks`**

Modifier `frontend/src/components/Navbar.jsx:33-38` :

```jsx
  const menuLinks = [
    { label: 'Accueil', path: '/' },
    { label: 'Fonctionnalités', path: '/#features' },
    { label: 'Témoignages', path: '/#testimonials' },
    { label: 'Avis', path: '/avis' },
    { label: 'Sécurité', path: '/security' }
  ]
```

- [ ] **Step 2: Vérifier manuellement dans le navigateur**

Ouvrir `http://localhost:5173/`, vérifier que "Avis" apparaît dans la nav desktop et dans le menu mobile (réduire la fenêtre ou DevTools responsive), et qu'il mène bien vers `/avis`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Navbar.jsx
git commit -m "feat: add Avis link to navbar"
```

---

## Task 7: Panneau admin — modération des avis

**Files:**
- Create: `frontend/src/pages/admin/AdminReviews.jsx`
- Modify: `frontend/src/pages/admin/AdminLayout.jsx`
- Modify: `frontend/src/App.jsx`

**Interfaces:**
- Consumes: `GET /api/admin/reviews` (avec `?status=`), `PATCH /api/admin/reviews/<id>`, `DELETE /api/admin/reviews/<id>` (Task 3), `authFetch` de `useAuth()`.

- [ ] **Step 1: Créer la page `AdminReviews.jsx`**

Créer `frontend/src/pages/admin/AdminReviews.jsx` :

```jsx
import { useEffect, useState, useCallback } from 'react'
import { Check, X, Trash2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const STATUS_OPTIONS = ['', 'pending', 'approved', 'rejected']

const STATUS_BADGE = {
  pending: 'bg-slate-800 text-slate-400',
  approved: 'bg-emerald-900/30 text-emerald-300',
  rejected: 'bg-red-900/30 text-red-300',
}

export default function AdminReviews() {
  const { authFetch } = useAuth()
  const [reviews, setReviews] = useState([])
  const [status, setStatus] = useState('pending')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadReviews = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const params = status ? `?status=${status}` : ''
      const res = await authFetch(`/api/admin/reviews${params}`)
      if (!res.ok) throw new Error('Erreur de chargement')
      setReviews(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [authFetch, status])

  useEffect(() => { loadReviews() }, [loadReviews])

  const updateStatus = async (review, newStatus) => {
    try {
      const res = await authFetch(`/api/admin/reviews/${review.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      if (!res.ok) throw new Error('Mise à jour impossible')
      setReviews((prev) => prev.filter((r) => r.id !== review.id))
    } catch (err) {
      alert(err.message)
    }
  }

  const handleDelete = async (review) => {
    if (!window.confirm(`Supprimer l'avis de ${review.user_email} ?`)) return
    try {
      const res = await authFetch(`/api/admin/reviews/${review.id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Suppression impossible')
      setReviews((prev) => prev.filter((r) => r.id !== review.id))
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Avis</h1>
        <p className="text-sm text-slate-400">{reviews.length} avis</p>
      </div>

      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
      >
        {STATUS_OPTIONS.map((s) => (
          <option key={s} value={s}>{s || 'Tous les statuts'}</option>
        ))}
      </select>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase tracking-wider">
              <th className="px-4 py-3">Utilisateur</th>
              <th className="px-4 py-3">Note</th>
              <th className="px-4 py-3">Texte</th>
              <th className="px-4 py-3">Statut</th>
              <th className="px-4 py-3">Créé le</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-slate-500">Chargement...</td></tr>
            ) : reviews.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-slate-500">Aucun avis</td></tr>
            ) : (
              reviews.map((review) => (
                <tr key={review.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-white">{review.display_name || review.user_email}</td>
                  <td className="px-4 py-3 text-slate-400">{review.rating}/5</td>
                  <td className="px-4 py-3 text-slate-400 max-w-xs truncate" title={review.text}>{review.text}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_BADGE[review.status] || 'bg-slate-800 text-slate-400'}`}>
                      {review.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(review.created_at).toLocaleDateString('fr-FR')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 justify-end">
                      <button
                        onClick={() => updateStatus(review, 'approved')}
                        className="p-2 text-slate-400 hover:text-emerald-400 transition-colors"
                        title="Approuver"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => updateStatus(review, 'rejected')}
                        className="p-2 text-slate-400 hover:text-orange-400 transition-colors"
                        title="Rejeter"
                      >
                        <X className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(review)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Ajouter l'entrée de navigation admin**

Modifier `frontend/src/pages/admin/AdminLayout.jsx` :

```jsx
import { LayoutDashboard, Users, ListChecks, MessageSquare, LogOut, ArrowLeft } from 'lucide-react'
```

(remplacer l'import `lucide-react` existant, ligne `frontend/src/pages/admin/AdminLayout.jsx:2`, en ajoutant `MessageSquare`), puis :

```jsx
const NAV_ITEMS = [
  { to: '/admin', end: true, icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/admin/users', icon: Users, label: 'Utilisateurs' },
  { to: '/admin/jobs', icon: ListChecks, label: 'Jobs' },
  { to: '/admin/reviews', icon: MessageSquare, label: 'Avis' },
]
```

- [ ] **Step 3: Ajouter la route admin**

Modifier `frontend/src/App.jsx` :

```jsx
import AdminJobs from './pages/admin/AdminJobs'
import AdminReviews from './pages/admin/AdminReviews'
```

(ajouter l'import juste après celui d'`AdminJobs`, ligne `frontend/src/App.jsx:19`), puis dans le bloc de routes `/admin` (ligne `frontend/src/App.jsx:54-60`) :

```jsx
          <Route path="/admin" element={<RequireStaff><AdminLayout /></RequireStaff>}>
            <Route index element={<AdminDashboard />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="users/new" element={<AdminUserForm />} />
            <Route path="users/:id" element={<AdminUserForm />} />
            <Route path="jobs" element={<AdminJobs />} />
            <Route path="reviews" element={<AdminReviews />} />
          </Route>
```

- [ ] **Step 4: Vérifier manuellement dans le navigateur**

Se connecter avec un compte staff (`python manage.py createsuperuser` si besoin), ouvrir `http://localhost:5173/admin/reviews` : la liste des avis `pending` doit s'afficher (y compris celui créé au Task 4). Cliquer sur "Approuver" : l'avis disparaît de la liste filtrée `pending`. Repasser le filtre sur "Tous les statuts" pour vérifier qu'il apparaît en `approved`. Vérifier ensuite qu'il apparaît sur la Landing page (`http://localhost:5173/`).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/admin/AdminReviews.jsx frontend/src/pages/admin/AdminLayout.jsx frontend/src/App.jsx
git commit -m "feat: add admin review moderation page"
```

---

## Task 8: Vérification finale bout-en-bout

**Files:** aucun (validation uniquement)

- [ ] **Step 1: Lancer toute la suite de tests backend**

```bash
cd backend_django
python manage.py test
```
Expected: `OK`, tous les tests passent (y compris `reviews` et `dashboard`).

- [ ] **Step 2: Lancer le linter frontend**

```bash
cd frontend
npm run lint 2>&1 || npx eslint src --ext .jsx,.js
```
Expected: aucune erreur bloquante sur les fichiers modifiés/créés (`Reviews.jsx`, `Landing.jsx`, `Navbar.jsx`, `AdminReviews.jsx`, `AdminLayout.jsx`, `App.jsx`).

- [ ] **Step 3: Parcours utilisateur complet en local**

Avec `python manage.py runserver` (backend_django, port 8000) et `npm run dev` (frontend, port 5173) lancés :
1. Créer un compte via `/register`.
2. Aller sur `/avis`, soumettre un avis (note + texte) → message "en attente de validation".
3. Se déconnecter, se reconnecter en staff, aller sur `/admin/reviews`, approuver l'avis.
4. Revenir sur `/` (Landing) : l'avis approuvé doit apparaître dans la section Testimonials.
5. Se reconnecter avec le compte initial, retourner sur `/avis`, modifier l'avis (nouvelle note/texte) → statut repasse à "en attente de validation" ; vérifier sur `/admin/reviews` que l'avis apparaît de nouveau en `pending` avec le contenu mis à jour.

Aucune étape ne doit produire d'erreur console navigateur ni d'erreur serveur Django.
