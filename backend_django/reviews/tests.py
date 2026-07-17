from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Review
from rest_framework.test import APITestCase

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
