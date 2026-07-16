from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est requis")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Utilisateur applicatif. Email comme identifiant (pas de username)."""

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Attribution captée une seule fois, à l'inscription (cf. décision produit :
    # pas de tracking par requête, pas de conservation de l'IP brute).
    signup_country = models.CharField(max_length=2, blank=True, help_text="Code pays ISO (ex: FR, US)")
    signup_referrer_domain = models.CharField(max_length=255, blank=True, help_text="Domaine du referrer HTTP (ex: facebook.com)")
    signup_utm_source = models.CharField(max_length=100, blank=True)
    signup_utm_medium = models.CharField(max_length=100, blank=True)
    signup_utm_campaign = models.CharField(max_length=100, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
