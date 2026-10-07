from django.contrib import admin
from .models import Booking


@admin.action(description="Move to 'company reviewing' (you're now checking worker availability)")
def mark_reviewing(modeladmin, request, queryset):
    queryset.filter(status="requested").update(status="company_reviewing")


@admin.action(description="Confirm worker availability -> 'worker confirmed' (client can now pay)")
def mark_worker_confirmed(modeladmin, request, queryset):
    queryset.filter(status="company_reviewing").update(status="worker_confirmed")


@admin.action(description="Decline booking (worker unavailable)")
def mark_declined(modeladmin, request, queryset):
    queryset.update(status="declined")


@admin.action(description="Start job -> 'in progress' (do this once payment has cleared)")
def mark_in_progress(modeladmin, request, queryset):
    queryset.filter(status="worker_confirmed").update(status="in_progress")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id", "client_name", "client_phone", "worker", "category",
        "status", "quoted_amount", "created_at",
    )
    list_filter = ("status", "category")
    search_fields = ("client_name", "client_phone", "worker__full_name", "tracking_code")
    readonly_fields = ("tracking_code", "created_at", "updated_at")
    actions = [mark_reviewing, mark_worker_confirmed, mark_declined, mark_in_progress]
