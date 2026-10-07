import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from bookings.models import Booking
from .models import Payment
from .serializers import PaymentSerializer
from . import paystack


class InitializePaymentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, tracking_code):
        booking = get_object_or_404(Booking, tracking_code=tracking_code)
        if booking.status != "worker_confirmed":
            return Response(
                {"detail": f"Booking isn't ready for payment yet (status: '{booking.status}')."},
                status=400,
            )
        if not booking.quoted_amount:
            return Response({"detail": "No quoted amount set on this booking yet."}, status=400)

        reference = f"WK-{booking.id}-{uuid.uuid4().hex[:8]}"
        commission = (booking.quoted_amount * Decimal(settings.PLATFORM_COMMISSION_PERCENT) / 100).quantize(Decimal("0.01"))
        payout = booking.quoted_amount - commission

        data = paystack.initialize_transaction(
            email=f"client{booking.id}@worka.app",
            amount_ghs=float(booking.quoted_amount),
            reference=reference,
            callback_url=f"{settings.FRONTEND_BASE_URL}/booking/{booking.tracking_code}/status",
            metadata={"booking_id": booking.id, "tracking_code": str(booking.tracking_code)},
        )

        payment, _ = Payment.objects.update_or_create(
            booking=booking,
            defaults={
                "amount": booking.quoted_amount,
                "commission_amount": commission,
                "payout_amount": payout,
                "paystack_reference": reference,
                "paystack_authorization_url": data["authorization_url"],
                "status": "pending",
            },
        )
        return Response(PaymentSerializer(payment).data)


class VerifyPaymentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, reference):
        payment = get_object_or_404(Payment, paystack_reference=reference)
        data = paystack.verify_transaction(reference)

        if data.get("status") == "success" and payment.status != "paid":
            payment.status = "paid"
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at"])
            payment.booking.status = "in_progress"
            payment.booking.save(update_fields=["status"])
        elif data.get("status") != "success":
            payment.status = "failed"
            payment.save(update_fields=["status"])

        return Response(PaymentSerializer(payment).data)


class PaystackWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event = request.data
        if event.get("event") == "charge.success":
            reference = event["data"]["reference"]
            try:
                payment = Payment.objects.get(paystack_reference=reference)
            except Payment.DoesNotExist:
                return Response(status=200)
            if payment.status != "paid":
                payment.status = "paid"
                payment.paid_at = timezone.now()
                payment.save(update_fields=["status", "paid_at"])
                payment.booking.status = "in_progress"
                payment.booking.save(update_fields=["status"])
        return Response(status=200)


class ReleaseEscrowView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, tracking_code):
        booking = get_object_or_404(Booking, tracking_code=tracking_code)
        payment = get_object_or_404(Payment, booking=booking)

        if booking.status != "paid_out":
            return Response(
                {"detail": "Client must confirm completion first (see /bookings/track/<code>/confirm-completion/)."},
                status=400,
            )
        if payment.status == "released":
            return Response(PaymentSerializer(payment).data)

        worker = booking.worker
        if not worker.momo_number:
            return Response({"detail": "Worker has no Mobile Money number on file — release manually."}, status=400)

        recipient = paystack.create_transfer_recipient(worker.full_name, worker.momo_number, worker.momo_network)
        paystack.initiate_transfer(
            recipient["recipient_code"],
            float(payment.payout_amount),
            reason=f"Worka payout — booking #{booking.id}",
        )
        payment.status = "released"
        payment.released_at = timezone.now()
        payment.save(update_fields=["status", "released_at"])
        return Response(PaymentSerializer(payment).data)
