from django.shortcuts import render

# Create your views here.
from decimal import Decimal, InvalidOperation

from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Coupon, CouponUsage, InterestRule, InstallmentPlan
from .services import calculate_emi, calculate_discount, money


class ApplyCouponAPIView(APIView):

    def post(self, request):
        data = request.data

        # 1. Validate principal.
        try:
            principal = Decimal(str(data.get("principal", "")))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"error": "A valid principal amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not principal.is_finite() or principal <= 0:
            return Response(
                {"error": "Principal must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Validate months.
        try:
            months = int(data.get("months"))
        except (TypeError, ValueError):
            return Response(
                {"error": "Months must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if months <= 0:
            return Response(
                {"error": "Months must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Validate interest rule.
        interest_rule_id = data.get("interest_rule_id")

        interest_rule = get_object_or_404(
            InterestRule,
            pk=interest_rule_id,
            is_active=True,
        )

        coupon_code = data.get("coupon_code")

        try:
            with transaction.atomic():

                coupon = None
                discount_amount = Decimal("0.00")
                discounted_principal = principal

                # 4. Apply coupon if supplied.
                if coupon_code:
                    normalized_code = str(coupon_code).strip().upper()

                    # Lock the coupon row to serialize competing requests.
                    coupon = (
                        Coupon.objects
                        .select_for_update()
                        .filter(code__iexact=normalized_code)
                        .first()
                    )

                    if coupon is None:
                        return Response(
                            {"error": "Invalid coupon code."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    if coupon.is_used:
                        return Response(
                            {"error": "This coupon has already been used."},
                            status=status.HTTP_409_CONFLICT,
                        )

                    if CouponUsage.objects.filter(coupon=coupon).exists():
                        return Response(
                            {"error": "This coupon has already been used."},
                            status=status.HTTP_409_CONFLICT,
                        )

                    discount_amount = calculate_discount(
                        principal,
                        coupon.discount,
                    )

                    discounted_principal = money(
                        principal - discount_amount
                    )

                    if discounted_principal <= 0:
                        return Response(
                            {
                                "error": (
                                    "Coupon discount must leave a positive "
                                    "principal amount."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # 5. Calculate EMI on the discounted principal.
                monthly_emi, total_payable = calculate_emi(
                    discounted_principal,
                    months,
                    interest_rule.annual_interest_rate,
                )

                # 6. Save installment plan.
                plan = InstallmentPlan.objects.create(
                    principal=principal,
                    months=months,
                    interest_rule=interest_rule,
                    coupon=coupon,
                    discount_amount=discount_amount,
                    monthly_emi=monthly_emi,
                    total_payable=total_payable,
                )

                # 7. Record usage and mark coupon used.
                if coupon:
                    CouponUsage.objects.create(
                        coupon=coupon,
                        installment_plan=plan,
                    )

                    coupon.is_used = True
                    coupon.save(update_fields=["is_used"])

                # 8. Return calculated values.
                return Response(
                    {
                        "message": "Coupon applied successfully.",
                        "installment_plan_id": plan.id,
                        "principal": str(money(principal)),
                        "discount_amount": str(discount_amount),
                        "discounted_principal": str(
                            money(discounted_principal)
                        ),
                        "annual_interest_rate": str(
                            interest_rule.annual_interest_rate
                        ),
                        "months": months,
                        "monthly_emi": str(monthly_emi),
                        "total_payable": str(total_payable),
                        "coupon_code": coupon.code if coupon else None,
                    },
                    status=status.HTTP_200_OK,
                )

        except IntegrityError:
            # A uniqueness constraint can reject a concurrent duplicate use.
            return Response(
                {"error": "This coupon has already been used."},
                status=status.HTTP_409_CONFLICT,
            )
