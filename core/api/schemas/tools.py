from ninja import Schema
from typing import Optional, List


class MortgageCalculatorIn(Schema):
    property_price: float
    down_payment: float
    interest_rate: float  # Annual interest rate in percentage
    loan_term_years: int = 30


class MortgageCalculatorOut(Schema):
    monthly_payment: float
    total_payment: float
    total_interest: float
    currency: str = "USD"


class ValuationIn(Schema):
    city_name: str
    property_type: str
    bedrooms: int
    bathrooms: int
    area: float  # in square meters
    amenities: Optional[List[str]] = None
    description: Optional[str] = None


class ValuationOut(Schema):
    estimated_price: float
    price_range_low: float
    price_range_high: float
    confidence_score: float  # 0 to 1
    reasoning: str
    currency: str = "USD"
