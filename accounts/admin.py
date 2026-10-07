from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Worker, OTP


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    model = Worker
    list_display = (
        "full_name", "phone_number", "category", "region", "town",
        "is_verified", "is_available", "rating_avg", "is_active",
    )
    list_filter = ("is_verified", "is_available", "region", "category")
    search_fields = ("full_name", "phone_number", "town")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Personal info", {"fields": (
            "full_name", "category", "bio", "years_of_experience", "region", "town",
            "latitude", "longitude", "profile_photo",
        )}),
        ("Verification (review ID before flipping is_verified)", {"fields": (
            "id_document_front", "id_document_back", "id_type", "is_verified", "verification_notes",
        )}),
        ("Availability & rating", {"fields": ("is_available", "rating_avg", "rating_count")}),
        ("Payout", {"fields": ("momo_number", "momo_network")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone_number", "full_name", "password1", "password2")}),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "code", "created_at", "is_used")
    readonly_fields = ("phone_number", "code", "created_at")
