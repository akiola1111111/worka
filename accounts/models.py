import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta

GHANA_REGIONS = [
    ("ashanti", "Ashanti"), ("greater_accra", "Greater Accra"), ("western", "Western"),
    ("western_north", "Western North"), ("central", "Central"), ("eastern", "Eastern"),
    ("volta", "Volta"), ("oti", "Oti"), ("northern", "Northern"),
    ("savannah", "Savannah"), ("north_east", "North East"), ("upper_east", "Upper East"),
    ("upper_west", "Upper West"), ("bono", "Bono"), ("bono_east", "Bono East"),
    ("ahafo", "Ahafo"),
]


class WorkerManager(BaseUserManager):
    def create_user(self, phone_number, full_name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("A phone number is required")
        worker = self.model(phone_number=phone_number, full_name=full_name, **extra_fields)
        if password:
            worker.set_password(password)
        else:
            worker.set_unusable_password()
        worker.save(using=self._db)
        return worker

    def create_superuser(self, phone_number, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        return self.create_user(phone_number, full_name, password, **extra_fields)


class Worker(AbstractBaseUser, PermissionsMixin):
    """
    A tradesperson registered on the platform. This is the AUTH_USER_MODEL —
    workers are the only party that logs in; clients never create accounts.

    NOTE: login is by phone number only (no SMS/OTP step) — see accounts/views.py.
    This is simpler for early testing, but means anyone who knows a worker's
    phone number can log into their account. Worth revisiting before a public
    launch (e.g. add a PIN, or bring OTP back using the OTP model below).
    """

    phone_number = models.CharField(max_length=15, unique=True, help_text="e.g. 0244123456")
    full_name = models.CharField(max_length=150)
    category = models.ForeignKey(
        "services.ServiceCategory", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="workers",
    )
    bio = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)

    region = models.CharField(max_length=30, choices=GHANA_REGIONS, blank=True)
    town = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    profile_photo = models.ImageField(upload_to="profile_photos/", null=True, blank=True)
    id_document_front = models.ImageField(upload_to="id_documents/", null=True, blank=True)
    id_document_back = models.ImageField(upload_to="id_documents/", null=True, blank=True)
    id_type = models.CharField(max_length=30, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)

    is_available = models.BooleanField(default=True)
    rating_avg = models.FloatField(default=0)
    rating_count = models.PositiveIntegerField(default=0)

    momo_number = models.CharField(max_length=15, blank=True)
    momo_network = models.CharField(
        max_length=20, blank=True,
        choices=[("mtn", "MTN"), ("vodafone", "Telecel/Vodafone"), ("airteltigo", "AirtelTigo")],
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = WorkerManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class OTP(models.Model):
    """
    Unused by the current login flow (login is phone-number-only, see
    accounts/views.py) — kept here in case OTP verification is switched back
    on later, so no migration is needed either way.
    """

    phone_number = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate(cls, phone_number):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(phone_number=phone_number, code=code)

    def is_valid(self):
        return not self.is_used and timezone.now() - self.created_at < timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.phone_number}"
