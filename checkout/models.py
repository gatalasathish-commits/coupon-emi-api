from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)

    # Discount is a percentage: 10 means 10%
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class InterestRule(models.Model):
    name = models.CharField(max_length=100)

    # Annual interest rate in percentage.
    # Example: 12.00 means 12% per year.
    annual_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class InstallmentPlan(models.Model):
    principal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    months = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    interest_rule = models.ForeignKey(
        InterestRule,
        on_delete=models.PROTECT,
        related_name="installment_plans",
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="installment_plans",
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    monthly_emi = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total_payable = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan #{self.pk}"


class CouponUsage(models.Model):
    coupon = models.OneToOneField(
        Coupon,
        on_delete=models.PROTECT,
        related_name="usage",
    )

    installment_plan = models.ForeignKey(
        InstallmentPlan,
        on_delete=models.PROTECT,
        related_name="coupon_usages",
    )

    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.coupon.code} - Plan #{self.installment_plan_id}"