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
