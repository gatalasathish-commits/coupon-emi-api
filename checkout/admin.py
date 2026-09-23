
from django.contrib import admin
from .models import Coupon, InterestRule, InstallmentPlan, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount", "is_used", "created_at")
    search_fields = ("code",)
    list_filter = ("is_used",)


@admin.register(InterestRule)
class InterestRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "annual_interest_rate", "is_active")
    list_filter = ("is_active",)


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "principal",
        "months",
        "monthly_emi",
        "total_payable",
        "coupon",
    )


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("coupon", "installment_plan", "used_at")