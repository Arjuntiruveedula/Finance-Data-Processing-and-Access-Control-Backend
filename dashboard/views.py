from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from finance.models import FinancialRecord
from core.permissions import DashboardPermission


class SummaryView(APIView):
    """
    Aggregated financial summary.
    Requires `finance.view_financialrecord` permission — grant this to any
    Group via the Django admin to allow that group to view the dashboard.
    """
    permission_classes = [permissions.IsAuthenticated, DashboardPermission]

    def get(self, request):
        qs = FinancialRecord.objects.filter(is_deleted=False)

        total_income = qs.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = qs.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0

        category_totals = list(qs.values('category', 'type').annotate(total=Sum('amount')).order_by('-total'))

        for cat in category_totals:
            cat['total'] = float(cat['total'])

        recent_activity = list(qs.order_by('-created_at')[:5].values('id', 'amount', 'type', 'category', 'date', 'created_at'))
        for act in recent_activity:
            act['amount'] = float(act['amount'])
            act['date'] = act['date'].isoformat() if act['date'] else None
            act['created_at'] = act['created_at'].isoformat() if act['created_at'] else None

        return Response({
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'net_balance': float(total_income - total_expense),
            'category_totals': category_totals,
            'recent_activity': recent_activity
        })


class TrendsView(APIView):
    """
    Monthly trend analysis.
    Requires `finance.view_financialrecord` permission.
    """
    permission_classes = [permissions.IsAuthenticated, DashboardPermission]

    def get(self, request):
        qs = FinancialRecord.objects.filter(is_deleted=False)

        trends = qs.annotate(month=TruncMonth('date')).values('month', 'type').annotate(total=Sum('amount')).order_by('month')

        formatted_trends = []
        for result in trends:
            formatted_trends.append({
                'month': result['month'].isoformat() if result['month'] else None,
                'type': result['type'],
                'total': float(result['total'])
            })

        return Response(formatted_trends)
