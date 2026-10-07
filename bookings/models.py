import uuid
from django.db import models
from accounts.models import Worker
from services.models import ServiceCategory


class Booking(models.Model):
    STATUS_CHOICES = [
        ("requested", "Requested — awaiting company review"),
        ("company_reviewing", "Company confirming worker availability"),
        ("worker_confirmed", "Worker confirmed — awaiting payment"),
        ("in_progress", "Job in progress"),
        ("completed", "Job marked complete — awaiting client release"),
        ("paid_out", "Payment released to worker"),
        ("declined", "Worker unavailable / declined"),
        ("cancelled", "Cancelled"),
    ]

    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    client_name = models.CharField(max_length=150)
    client_phone = models.CharField(max_length=15)
    client_location_text = models.CharField(max_length=255, blank=True)
    client_latitude = models.FloatField(null=True, blank=True)
    client_longitude = models.FloatField(null=True, blank=True)

    worker = models.ForeignKey(Worker, on_delete=models.PROTECT, related_name="bookings")
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT)
    description = models.TextField()
    preferred_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="requested")
    quoted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.id} — {self.client_name} -> {self.worker.full_name} ({self.status})"
