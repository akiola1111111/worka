from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from accounts.models import Worker, GHANA_REGIONS
from accounts.utils import haversine_km
from bookings.models import Booking
from payments import services
from services.models import ServiceCategory


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# =====================================================================
# CLIENT-FACING SITE — no account, ever.
# =====================================================================

def home(request):
    categories = ServiceCategory.objects.filter(is_active=True)
    category_id = request.GET.get("category", "")
    region = request.GET.get("region", "")
    lat, lng = _float(request.GET.get("lat")), _float(request.GET.get("lng"))
    searched = "searched" in request.GET

    workers = []
    if searched:
        qs = Worker.objects.filter(is_active=True, is_staff=False).select_related("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        if region:
            qs = qs.filter(region=region)
        for w in qs:
            w.distance_km = haversine_km(lat, lng, w.latitude, w.longitude) if lat is not None and lng is not None else None
            workers.append(w)
        workers.sort(key=lambda w: (w.distance_km is None, w.distance_km or 0, not w.is_verified))

    return render(request, "web/home.html", {
        "categories": categories, "regions": GHANA_REGIONS, "workers": workers,
        "category_id": category_id, "region": region, "lat": lat, "lng": lng,
        "searched": searched,
    })


def worker_detail(request, pk):
    worker = get_object_or_404(Worker, pk=pk, is_active=True, is_staff=False)
    lat, lng = _float(request.GET.get("lat")), _float(request.GET.get("lng"))
    distance = haversine_km(lat, lng, worker.latitude, worker.longitude) if lat is not None and lng is not None else None

    if request.method == "POST":
        name = request.POST.get("client_name", "").strip()
        phone = request.POST.get("client_phone", "").strip()
        place = request.POST.get("client_location_text", "").strip()
        description = request.POST.get("description", "").strip()
        if not (name and phone and place and description):
            messages.error(request, "Please fill in your name, phone number, location and job details.")
        elif not worker.category:
            messages.error(request, "This worker hasn't set a trade yet.")
        else:
            booking = Booking.objects.create(
                client_name=name, client_phone=phone, client_location_text=place,
                client_latitude=lat, client_longitude=lng, worker=worker,
                category=worker.category, description=description,
                preferred_date=request.POST.get("preferred_date") or None,
            )
            return redirect("web:booking_status", tracking_code=booking.tracking_code)

    return render(request, "web/worker_detail.html", {
        "worker": worker, "distance": distance, "lat": lat, "lng": lng,
        "form": request.POST,
    })


STEPS = [
    ("requested", "Request sent"),
    ("company_reviewing", "Worka is checking the worker's availability"),
    ("worker_confirmed", "Worker confirmed - ready for payment"),
    ("in_progress", "Job in progress"),
    ("completed", "Job finished - your review needed"),
    ("paid_out", "Payment released to worker"),
]


def booking_status(request, tracking_code):
    booking = get_object_or_404(Booking.objects.select_related("worker", "category"), tracking_code=tracking_code)
    keys = [k for k, _ in STEPS]
    current = keys.index(booking.status) if booking.status in keys else -1
    steps = [{"label": label, "done": i <= current} for i, (_, label) in enumerate(STEPS)]
    return render(request, "web/booking_status.html", {"booking": booking, "steps": steps})


@require_POST
def pay(request, tracking_code):
    booking = get_object_or_404(Booking, tracking_code=tracking_code)
    if booking.status != "worker_confirmed" or not booking.quoted_amount:
        messages.error(request, "This booking isn't ready for payment yet.")
        return redirect("web:booking_status", tracking_code=tracking_code)
    callback = request.build_absolute_uri(reverse("web:payment_callback", args=[tracking_code]))
    try:
        url = services.start_payment(booking, callback)
    except Exception:
        messages.error(request, "We couldn't start the payment. Please try again in a moment.")
        return redirect("web:booking_status", tracking_code=tracking_code)
    return redirect(url)


def payment_callback(request, tracking_code):
    booking = get_object_or_404(Booking, tracking_code=tracking_code)
    reference = request.GET.get("reference") or request.GET.get("trxref")
    if reference and hasattr(booking, "payment") and booking.payment.paystack_reference == reference:
        try:
            payment = services.confirm_payment(reference)
            if payment.status == "paid":
                messages.success(request, "Payment received. Worka is holding it safely until your job is done.")
            else:
                messages.error(request, "Payment didn't go through. You can try again.")
        except Exception:
            messages.error(request, "We couldn't confirm your payment yet. Refresh in a minute, or contact Worka.")
    return redirect("web:booking_status", tracking_code=tracking_code)


@require_POST
def confirm_completion(request, tracking_code):
    booking = get_object_or_404(Booking, tracking_code=tracking_code)
    if booking.status != "completed":
        messages.error(request, "The worker hasn't marked this job as finished yet.")
    else:
        try:
            services.release_to_worker(booking)
            messages.success(request, "Thank you! Payment has been released to the worker.")
        except Exception as exc:
            messages.error(request, f"We couldn't release the payment automatically ({exc}). The Worka team will finish it manually.")
    return redirect("web:booking_status", tracking_code=tracking_code)


# =====================================================================
# WORKER PORTAL — login is by phone number only, no verification code.
# (See the note on accounts.models.Worker for the tradeoff this makes.)
# =====================================================================

def portal_register(request):
    if request.method == "POST":
        phone = request.POST.get("phone_number", "").strip()
        name = request.POST.get("full_name", "").strip()
        category_id = request.POST.get("category")
        region = request.POST.get("region", "")
        town = request.POST.get("town", "").strip()
        momo_number = request.POST.get("momo_number", "").strip()
        momo_network = request.POST.get("momo_network", "mtn")

        if not (phone and name and category_id and region and town):
            messages.error(request, "Please fill in every field.")
        elif Worker.objects.filter(phone_number=phone).exists():
            messages.error(request, "That phone number is already registered. Try logging in instead.")
        else:
            worker = Worker.objects.create_user(
                phone_number=phone, full_name=name, category_id=category_id,
                region=region, town=town, momo_number=momo_number, momo_network=momo_network,
            )
            auth_login(request, worker, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Welcome to Worka!")
            return redirect("web:portal_dashboard")

    return render(request, "web/portal_register.html", {
        "categories": ServiceCategory.objects.filter(is_active=True),
        "regions": GHANA_REGIONS,
        "form": request.POST,
    })


def portal_login(request):
    if request.method == "POST":
        phone = request.POST.get("phone_number", "").strip()
        worker = Worker.objects.filter(phone_number=phone).first()
        if not worker:
            messages.error(request, "No worker registered with that number yet.")
        else:
            auth_login(request, worker, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("web:portal_dashboard")
    return render(request, "web/portal_login.html")


def portal_logout(request):
    auth_logout(request)
    return redirect("web:portal_login")


@login_required(login_url="web:portal_login")
def portal_dashboard(request):
    worker = request.user
    bookings = Booking.objects.filter(worker=worker).select_related("category")
    return render(request, "web/portal_dashboard.html", {"worker": worker, "bookings": bookings})


@login_required(login_url="web:portal_login")
@require_POST
def portal_toggle_availability(request):
    worker = request.user
    worker.is_available = not worker.is_available
    worker.save(update_fields=["is_available"])
    return redirect("web:portal_dashboard")


@login_required(login_url="web:portal_login")
def portal_id_upload(request):
    worker = request.user
    if request.method == "POST":
        worker.id_type = request.POST.get("id_type", worker.id_type)
        if request.FILES.get("id_document_front"):
            worker.id_document_front = request.FILES["id_document_front"]
        if request.FILES.get("id_document_back"):
            worker.id_document_back = request.FILES["id_document_back"]
        worker.save()
        messages.success(request, "Uploaded. Worka's team will review it shortly.")
        return redirect("web:portal_dashboard")
    return render(request, "web/portal_id_upload.html", {"worker": worker})


@login_required(login_url="web:portal_login")
def portal_booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk, worker=request.user)
    return render(request, "web/portal_booking_detail.html", {"booking": booking})


@login_required(login_url="web:portal_login")
@require_POST
def portal_mark_complete(request, pk):
    booking = get_object_or_404(Booking, pk=pk, worker=request.user)
    if booking.status == "in_progress":
        booking.status = "completed"
        booking.completed_at = timezone.now()
        booking.save(update_fields=["status", "completed_at"])
        messages.success(request, "Marked complete — the client will confirm and release payment.")
    return redirect("web:portal_booking_detail", pk=pk)
