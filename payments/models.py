from django.db import models
from bookings.models import Booking


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending — client hasn't paid yet"),
        ("paid", "Paid — held by the company"),
        ("released", "Released — paid out to the worker"),
        ("refunded", "Refunded to client"),
        ("failed", "Failed"),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    paystack_reference = models.CharField(max_length=100, unique=True)
    paystack_authorization_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    paid_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for booking #{self.booking_id} — {self.status} (GHS {self.amount})"
