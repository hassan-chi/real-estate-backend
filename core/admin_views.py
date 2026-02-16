from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from core.models import PropertyRequest, Subscription, Property

User = get_user_model()

from django.db.models.functions import TruncMonth
from django.core.serializers.json import DjangoJSONEncoder
import json

@staff_member_required
def analytics_dashboard(request):
    if not request.user.is_superuser:
        return render(request, "admin/403.html", status=403)

    # 1. Agent Performance
    agents = User.objects.filter(role=User.Role.AGENT).annotate(
        total_requests=Count('assigned_requests'),
        closed_requests=Count('assigned_requests', filter=Q(assigned_requests__status=PropertyRequest.RequestStatus.CLOSED)),
        in_progress_requests=Count('assigned_requests', filter=Q(assigned_requests__status=PropertyRequest.RequestStatus.IN_PROGRESS)),
        new_requests=Count('assigned_requests', filter=Q(assigned_requests__status=PropertyRequest.RequestStatus.NEW)),
    ).order_by('-total_requests')

    # Data for Agent Chart
    agent_names = [a.username for a in agents]
    agent_closed = [a.closed_requests for a in agents]
    agent_active = [a.in_progress_requests for a in agents]

    # 2. Revenue & Analytics
    total_subscription_revenue = Subscription.objects.aggregate(total=Sum('price'))['total'] or 0
    active_subscriptions = Subscription.objects.filter(active=True).count()
    
    # Monthly Revenue Trend
    monthly_revenue = Subscription.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('price')).order_by('month')
    
    chart_months = [entry['month'].strftime('%Y-%m') for entry in monthly_revenue] if monthly_revenue else []
    chart_revenue = [float(entry['total']) for entry in monthly_revenue] if monthly_revenue else []
    
    # 3. Property Stats
    total_listings = Property.objects.count()
    sold_listings = Property.objects.filter(status=Property.PropertyStatus.SOLD).count()
    rented_listings = Property.objects.filter(status=Property.PropertyStatus.RENTED).count()
    available_listings = Property.objects.filter(status=Property.PropertyStatus.AVAILABLE).count()

    # potential revenue from sales (if we had commission, for now just GTV)
    total_sales_volume = Property.objects.filter(status=Property.PropertyStatus.SOLD).aggregate(total=Sum('price'))['total'] or 0

    context = {
        "title": "Analytics Dashboard",
        "agents": agents,
        "revenue": {
            "total_subscription": total_subscription_revenue,
            "active_subs": active_subscriptions,
            "sales_volume": total_sales_volume,
        },
        "listings": {
            "total": total_listings,
            "sold": sold_listings,
            "rented": rented_listings,
        },
        # Chart Data
        "chart_data": json.dumps({
            "agent_names": agent_names,
            "agent_closed": agent_closed,
            "agent_active": agent_active,
            "months": chart_months,
            "revenue": chart_revenue,
            "listing_status": [available_listings, sold_listings, rented_listings],
        }, cls=DjangoJSONEncoder),
        # For breadcrumbs in admin template
        "site_header": "Real Estate Admin",
        "has_permission": True,
    }
    return render(request, "admin/analytics_dashboard.html", context)
