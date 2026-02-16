from ninja import Router
from core.api.auth import GlobalAuth
from core.api.schemas.tools import (
    MortgageCalculatorIn, MortgageCalculatorOut,
    ValuationIn, ValuationOut
)
from core.models import Property, City, Region
from django.db.models import Avg, Sum
from typing import List, Optional

router = Router(tags=["tools"])


@router.post("/mortgage-calculator", response=MortgageCalculatorOut)
def calculate_mortgage(request, payload: MortgageCalculatorIn):
    """
    Calculate monthly mortgage payments.
    Formula: M = P * (r * (1 + r)^n) / ((1 + r)^n - 1)
    """
    principal = payload.property_price - payload.down_payment
    if principal <= 0:
        return {
            "monthly_payment": 0,
            "total_payment": 0,
            "total_interest": 0,
            "currency": "USD"
        }
        
    monthly_rate = (payload.interest_rate / 100) / 12
    num_payments = payload.loan_term_years * 12
    
    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (
            (monthly_rate * (1 + monthly_rate) ** num_payments) / 
            ((1 + monthly_rate) ** num_payments - 1)
        )
        
    total_payment = monthly_payment * num_payments
    total_interest = total_payment - principal
    
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "currency": "USD"
    }


@router.post("/valuation", auth=GlobalAuth(), response=ValuationOut)
def estimate_property_value(request, payload: ValuationIn):
    similar_properties = Property.objects.filter(
        city__name__icontains=payload.city_name,
        price__gt=0,
        area__gt=0
    )
    
    # 2. Calculate average price per square meter
    if similar_properties.exists():
        metrics = similar_properties.aggregate(
            total_price=Sum('price'),
            total_area=Sum('area')
        )
        avg_price_per_sqm = metrics['total_price'] / metrics['total_area']
        source = f"based on {similar_properties.count()} properties in {payload.city_name}"
    else:
        # Fallback if no data found for this city
        # Default to $1,200 per sqm (adjust as needed for Iraq market)
        avg_price_per_sqm = 1200.0
        source = "based on national average (no local data found)"
        
    # 3. Base Calculation
    estimated_price = avg_price_per_sqm * payload.area
    
    # 4. Apply "Smart" Adjustments based on inputs
    reasoning_parts = [f"Base value calculated at ${int(avg_price_per_sqm)}/m² {source}."]
    
    # Adjust for bedrooms (Standard is ~3 for 150m, adjust slightly)
    # This is just a heuristic for the demo
    if payload.bedrooms > 4:
        estimated_price *= 1.15
        reasoning_parts.append("High bedroom count increases value by 15%.")
    elif payload.bedrooms < 2:
        estimated_price *= 0.95
        reasoning_parts.append("Fewer bedrooms slightly reduces estimate.")
        
    # Adjust for amenities
    if payload.amenities:
        # Simple keyword matching
        premium_keywords = ['pool', 'gym', 'garden', 'garage', 'balcony']
        amenity_bonus = 0
        found_premiums = []
        
        for amenity in payload.amenities:
            if any(k in amenity.lower() for k in premium_keywords):
                amenity_bonus += 0.05
                found_premiums.append(amenity)
                
        # Cap amenity bonus at 20%
        amenity_bonus = min(amenity_bonus, 0.20)
        
        if amenity_bonus > 0:
            estimated_price *= (1 + amenity_bonus)
            reasoning_parts.append(f"Premium amenities ({', '.join(found_premiums)}) added {int(amenity_bonus*100)}% value.")

    # 5. Final Formatting
    estimated_price = round(estimated_price, -2) # Round to nearest 100
    low_estimate = estimated_price * 0.9
    high_estimate = estimated_price * 1.1
    
    reasoning = " ".join(reasoning_parts)
    
    # Calculate confidence
    # More data points = higher confidence
    count = similar_properties.count() if similar_properties.exists() else 0
    confidence = min(0.9, 0.4 + (count * 0.05))
    
    return {
        "estimated_price": estimated_price,
        "price_range_low": round(low_estimate, -2),
        "price_range_high": round(high_estimate, -2),
        "confidence_score": confidence,
        "reasoning": reasoning,
        "currency": "USD"
    }
