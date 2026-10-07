from django.urls import path
from . import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("worker/<int:pk>/", views.worker_detail, name="worker_detail"),
    path("booking/<uuid:tracking_code>/", views.booking_status, name="booking_status"),
    path("booking/<uuid:tracking_code>/pay/", views.pay, name="pay"),
    path("booking/<uuid:tracking_code>/payment-callback/", views.payment_callback, name="payment_callback"),
    path("booking/<uuid:tracking_code>/confirm/", views.confirm_completion, name="confirm_completion"),

    path("portal/register/", views.portal_register, name="portal_register"),
    path("portal/login/", views.portal_login, name="portal_login"),
    path("portal/logout/", views.portal_logout, name="portal_logout"),
    path("portal/", views.portal_dashboard, name="portal_dashboard"),
    path("portal/availability/", views.portal_toggle_availability, name="portal_toggle_availability"),
    path("portal/id-upload/", views.portal_id_upload, name="portal_id_upload"),
    path("portal/booking/<int:pk>/", views.portal_booking_detail, name="portal_booking_detail"),
    path("portal/booking/<int:pk>/complete/", views.portal_mark_complete, name="portal_mark_complete"),
]
