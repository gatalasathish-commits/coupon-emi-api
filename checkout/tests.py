from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from .models import Coupon, CouponUsage, InterestRule, InstallmentPlan
from .services import calculate_emi, calculate_discount


@pytest.mark.django_db
def test_zero_interest_emi():
    emi, total = calculate_emi(
        Decimal("12000.00"),
        12,
        Decimal("0.00"),
    )

    assert emi == Decimal("1000.00")
    assert total == Decimal("12000.00")


@pytest.mark.django_db
def test_discount_calculation():
    discount = calculate_discount(
        Decimal("12000.00"),
        Decimal("10.00"),
    )

    assert discount == Decimal("1200.00")


@pytest.mark.django_db
def test_reducing_balance_emi():
    emi, total = calculate_emi(
        Decimal("12000.00"),
        12,
        Decimal("12.00"),
    )

    # Monthly rate = 1%; standard reducing-balance EMI.
    assert emi == Decimal("1066.19")
    assert total == Decimal("12794.28")


@pytest.mark.django_db
def test_coupon_application():
    client = APIClient()

    rule = InterestRule.objects.create(
        name="Zero Interest",
        annual_interest_rate=Decimal("0.00"),
    )

    coupon = Coupon.objects.create(
        code="SAVE10",
        discount=Decimal("10.00"),
    )

    response = client.post(
        "/api/v1/checkout/apply-coupon",
        {
            "principal": "12000.00",
            "months": 12,
            "interest_rule_id": rule.id,
            "coupon_code": "SAVE10",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["discount_amount"] == "1200.00"
    assert response.data["discounted_principal"] == "10800.00"
    assert response.data["monthly_emi"] == "900.00"
    assert response.data["total_payable"] == "10800.00"

    coupon.refresh_from_db()

    assert coupon.is_used is True
    assert CouponUsage.objects.filter(coupon=coupon).count() == 1
    assert InstallmentPlan.objects.count() == 1


@pytest.mark.django_db
def test_coupon_cannot_be_used_twice():
    client = APIClient()

    rule = InterestRule.objects.create(
        name="Zero Interest",
        annual_interest_rate=Decimal("0.00"),
    )

    Coupon.objects.create(
        code="SAVE10",
        discount=Decimal("10.00"),
    )

    payload = {
        "principal": "12000.00",
        "months": 12,
        "interest_rule_id": rule.id,
        "coupon_code": "SAVE10",
    }

    first_response = client.post(
        "/api/v1/checkout/apply-coupon",
        payload,
        format="json",
    )

    second_response = client.post(
        "/api/v1/checkout/apply-coupon",
        payload,
        format="json",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409

    assert InstallmentPlan.objects.count() == 1
    assert CouponUsage.objects.count() == 1


@pytest.mark.django_db
def test_invalid_coupon_returns_400():
    client = APIClient()

    rule = InterestRule.objects.create(
        name="Standard",
        annual_interest_rate=Decimal("12.00"),
    )

    response = client.post(
        "/api/v1/checkout/apply-coupon",
        {
            "principal": "12000.00",
            "months": 12,
            "interest_rule_id": rule.id,
            "coupon_code": "NOTREAL",
        },
        format="json",
    )

    assert response.status_code == 400
    assert InstallmentPlan.objects.count() == 0


@pytest.mark.django_db
def test_negative_principal_is_rejected():
    client = APIClient()

    rule = InterestRule.objects.create(
        name="Standard",
        annual_interest_rate=Decimal("12.00"),
    )

    response = client.post(
        "/api/v1/checkout/apply-coupon",
        {
            "principal": "-100.00",
            "months": 12,
            "interest_rule_id": rule.id,
        },
        format="json",
    )

    assert response.status_code == 400
    assert InstallmentPlan.objects.count() == 0
