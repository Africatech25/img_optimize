import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# Caractères de contrôle interdits dans les champs texte libres (tabulation
# et retours à la ligne compris : un nom affiché reste une seule ligne).
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE_RUN_RE = re.compile(r"\s+")


def normalize_email(value: str) -> str:
    """Email mis entièrement en minuscule (local part + domaine) et sans
    espaces superflus. Contrairement à BaseUserManager.normalize_email (qui
    ne touche qu'au domaine), on veut ici qu'une même adresse tapée avec une
    casse différente désigne toujours le même compte, à l'inscription comme
    à la connexion."""
    return value.strip().lower()


def clean_free_text(value: str) -> str:
    value = _CONTROL_CHARS_RE.sub(" ", value)
    value = _WHITESPACE_RUN_RE.sub(" ", value)
    return value.strip()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "date_joined", "is_staff"]


class AdminUserSerializer(serializers.ModelSerializer):
    """Utilisé par le panneau d'administration (liste + détail)."""

    jobs_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "display_name", "is_active", "is_staff", "is_superuser",
            "date_joined", "last_login", "jobs_count",
            "signup_country", "signup_referrer_domain",
            "signup_utm_source", "signup_utm_medium", "signup_utm_campaign",
        ]
        read_only_fields = ["date_joined", "last_login"]


class AdminUserWriteSerializer(serializers.ModelSerializer):
    """Création/édition d'un utilisateur depuis le panneau d'administration.
    Le mot de passe est optionnel à l'édition (laisser vide = inchangé)."""

    email = serializers.EmailField(max_length=254, validators=[])
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        min_length=8, max_length=128,
    )
    display_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "email", "password", "display_name", "is_active", "is_staff", "is_superuser"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        value = normalize_email(value)
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value

    def validate_display_name(self, value):
        return clean_free_text(value)

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    # validators=[] : l'unicité est vérifiée dans validate_email (message FR)
    email = serializers.EmailField(max_length=254, validators=[])
    password = serializers.CharField(write_only=True, min_length=8, max_length=128, validators=[validate_password])
    display_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "password", "display_name"]

    def validate_email(self, value):
        value = normalize_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value

    def validate_display_name(self, value):
        return clean_free_text(value)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Ajoute les infos utilisateur dans la réponse de connexion, et
    normalise l'email (espaces/casse) avant authentification — cohérent
    avec la normalisation appliquée à l'inscription."""

    def validate(self, attrs):
        username_field = User.USERNAME_FIELD
        if username_field in attrs and isinstance(attrs[username_field], str):
            attrs[username_field] = normalize_email(attrs[username_field])

        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
