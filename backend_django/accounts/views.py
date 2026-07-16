from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .geo import extract_referrer_domain, get_client_ip, lookup_country_code
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer, clean_free_text


class RegisterThrottle(ScopedRateThrottle):
    scope = "register"


class LoginThrottle(ScopedRateThrottle):
    scope = "login"


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Attribution : capté une seule fois, à l'inscription (cf. décision
        # produit). Best effort — ne doit jamais faire échouer l'inscription.
        user.signup_country = lookup_country_code(get_client_ip(request))
        user.signup_referrer_domain = extract_referrer_domain(
            clean_free_text(str(request.data.get("referrer", "")))[:255]
        )
        user.signup_utm_source = clean_free_text(str(request.data.get("utm_source", "")))[:100]
        user.signup_utm_medium = clean_free_text(str(request.data.get("utm_medium", "")))[:100]
        user.signup_utm_campaign = clean_free_text(str(request.data.get("utm_campaign", "")))[:100]
        user.save(update_fields=[
            "signup_country", "signup_referrer_domain",
            "signup_utm_source", "signup_utm_medium", "signup_utm_campaign",
        ])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (KeyError, TokenError):
            return Response({"detail": "Refresh token invalide ou manquant."}, status=400)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
