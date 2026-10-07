import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Payment
from . import paystack


def start_payment(booking, callback_url):
    reference = f"WK-{booking.id}-{uuid.uuid4().hex[:8]}"
    commission = (
        booking.quoted_amount * Decimal(settings.PLATFORM_COMMISSION_PERCENT) / 100
    ).quantize(Decimal("0.01"))
    data = paystack.initialize_transaction(
        email=f"client{booking.id}@worka.app",
        amount_ghs=float(booking.quoted_amount),
        reference=reference,
        callback_url=callback_url,
        metadata={"booking_id": booking.id},
    )
    Payment.objects.update_or_create(
        booking=booking,
        defaults={
            "amount": booking.quoted_amount,
            "commission_amount": commission,
            "payout_amount": booking.quoted_amount - commission,
            "paystack_reference": reference,
            "paystack_authorization_url": data["authorization_url"],
            "status": "pending",
        },
    )
    return data["authorization_url"]


def confirm_payment(reference):
    payment = Payment.objects.select_related("booking").get(paystack_reference=reference)
    data = paystack.verify_transaction(reference)
    if data.get("status") == "success":
        if payment.status != "paid":
            payment.status = "paid"
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at"])
            payment.booking.status = "in_progress"
            payment.booking.save(update_fields=["status"])
    else:
        payment.status = "failed"
        payment.save(update_fields=["status"])
    return payment


def release_to_worker(booking):
    payment = booking.payment
    worker = booking.worker
    if not worker.momo_number:
        raise ValueError("The worker has no Mobile Money number on file.")
    recipient = paystack.create_transfer_recipient(
        worker.full_name, worker.momo_number, worker.momo_network
    )
    paystack.initiate_transfer(
        recipient["recipient_code"], float(payment.payout_amount),
        reason=f"Worka payout - booking #{booking.id}",
    )
    payment.status = "released"
    payment.released_at = timezone.now()
    payment.save(update_fields=["status", "released_at"])
    booking.status = "paid_out"
    booking.save(update_fields=["status"])
