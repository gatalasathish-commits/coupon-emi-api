from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")
ONE_HUNDRED = Decimal("100")


def money(value):
    """
    Round a monetary value to two decimal places.
    """
    return Decimal(value).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )


def calculate_emi(principal, months, annual_interest_rate):
    """
    Calculate monthly EMI using the standard reducing-balance formula.

    principal: Amount financed.
    months: Number of monthly installments.
    annual_interest_rate: Annual percentage rate.

    Returns:
        (monthly_emi, total_payable)
    """

    principal = Decimal(principal)
    annual_interest_rate = Decimal(annual_interest_rate)

    if principal <= 0:
        raise ValueError("Principal must be greater than zero.")

    if months <= 0:
        raise ValueError("Months must be greater than zero.")

    if annual_interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    # Convert annual percentage rate to monthly decimal rate.
    monthly_rate = annual_interest_rate / ONE_HUNDRED / Decimal("12")

    # Zero-interest EMI.
    if monthly_rate == 0:
        monthly_emi = money(principal / Decimal(months))
        total_payable = money(principal)

        return monthly_emi, total_payable

    # Standard reducing-balance EMI formula:
    #
    # EMI = P * r * (1+r)^n / ((1+r)^n - 1)

    factor = (Decimal("1") + monthly_rate) ** months

    emi = principal * monthly_rate * factor / (factor - Decimal("1"))

    monthly_emi = money(emi)

    # Total based on the rounded monthly installment.
    total_payable = money(monthly_emi * months)

    return monthly_emi, total_payable


def calculate_discount(principal, discount_percentage):
    """
    Calculate percentage discount on the principal.
    """

    principal = Decimal(principal)
    discount_percentage = Decimal(discount_percentage)

    if principal <= 0:
        raise ValueError("Principal must be greater than zero.")

    if not Decimal("0") <= discount_percentage <= ONE_HUNDRED:
        raise ValueError("Discount must be between 0 and 100.")

    discount_amount = principal * discount_percentage / ONE_HUNDRED

    return money(discount_amount)