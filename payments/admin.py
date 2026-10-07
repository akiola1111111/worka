from django.contrib import admin
from django.utils import timezone
from .models import Payment


@admin.action(description="Mark as paid out manually (you sent the worker their money yourself)")
def mark_released_manually(modeladmin, request, queryset):
    for payment in queryset.filter(status="paid"):
        payment.status = "released"
        payment.released_at = timezone.now()
        payment.save(update_fields=["status", "released_at"])
        payment.booking.status = "paid_out"
        payment.booking.save(update_fields=["status"])


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "amount", "commission_amount", "payout_amount", "status", "paid_at", "released_at")
    list_filter = ("status",)
    search_fields = ("booking__client_name", "paystack_reference")
    readonly_fields = ("paystack_reference", "created_at")
    actions = [mark_released_manually]
