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
