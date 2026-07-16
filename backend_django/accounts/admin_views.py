from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .serializers import AdminUserSerializer, AdminUserWriteSerializer

User = get_user_model()


class AdminUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = User.objects.annotate(jobs_count=Count("optimization_jobs")).order_by("-date_joined")
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(display_name__icontains=q))
        return qs

    def get_serializer_class(self):
        return AdminUserWriteSerializer if self.request.method == "POST" else AdminUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.jobs_count = 0
        return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = User.objects.annotate(jobs_count=Count("optimization_jobs"))

    def get_serializer_class(self):
        return AdminUserSerializer if self.request.method == "GET" else AdminUserWriteSerializer

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        return Response(AdminUserSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            return Response(
                {"detail": "Vous ne pouvez pas supprimer votre propre compte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)
