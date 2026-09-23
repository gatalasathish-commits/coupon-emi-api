from django.urls import path

from .views import ApplyCouponAPIView


urlpatterns = [
    path(
        "apply-coupon",
        ApplyCouponAPIView.as_view(),
        name="apply-coupon",
    ),
]