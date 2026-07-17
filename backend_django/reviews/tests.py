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
