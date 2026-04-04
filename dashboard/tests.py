from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from finance.models import FinancialRecord
import datetime
from decimal import Decimal

User = get_user_model()


class DashboardAPITests(TestCase):
    """Tests for the aggregate Dashboard API views."""

    def setUp(self):
        self.client = APIClient()

        # Admin group with view permission
        ct = ContentType.objects.get(app_label='finance', model='financialrecord')
        view_perm = Permission.objects.get(content_type=ct, codename='view_financialrecord')

        admin_group, _ = Group.objects.get_or_create(name='Admin')
        admin_group.permissions.add(view_perm)

        # Viewer group — no permissions (should be denied)
        viewer_group, _ = Group.objects.get_or_create(name='Viewer')

        self.admin = User.objects.create_superuser(username='admin', password='123')
        self.admin.groups.set([admin_group])

        self.viewer = User.objects.create_user(username='viewer', password='123')
        self.viewer.groups.set([viewer_group])

        # Setup data
        FinancialRecord.objects.create(user=self.admin, amount=Decimal('500.00'), type='Income', category='Business', date=datetime.date(2025, 1, 15))
        FinancialRecord.objects.create(user=self.admin, amount=Decimal('100.00'), type='Expense', category='Supplies', date=datetime.date(2025, 1, 20))
        FinancialRecord.objects.create(user=self.viewer, amount=Decimal('1000.00'), type='Income', category='Salary', date=datetime.date(2025, 2, 10))
        FinancialRecord.objects.create(user=self.viewer, amount=Decimal('200.00'), type='Expense', category='Groceries', date=datetime.date(2025, 2, 15))

    def test_summary_view_admin(self):
        """Admin (with view_financialrecord) sees global aggregates."""
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_income'], 1500.00)
        self.assertEqual(res.data['total_expense'], 300.00)
        self.assertEqual(res.data['net_balance'], 1200.00)

    def test_summary_view_viewer_denied(self):
        """Viewer (without view_financialrecord) is blocked from the dashboard."""
        self.client.force_authenticate(user=self.viewer)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_trends_view(self):
        """Trends endpoint returns properly grouped monthly data."""
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/dashboard/trends/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(res.data, list))
        self.assertGreaterEqual(len(res.data), 1)
        first_item = res.data[0]
        self.assertIn('month', first_item)
        self.assertIn('total', first_item)
        self.assertIn('type', first_item)
