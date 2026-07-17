from django.urls import path

from . import views

urlpatterns = [
    path("public", views.PublicReviewListView.as_view()),
    path("me", views.MyReviewView.as_view()),
]
