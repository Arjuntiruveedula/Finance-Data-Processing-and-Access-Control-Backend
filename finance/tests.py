from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from .models import FinancialRecord
from decimal import Decimal
import datetime

User = get_user_model()


def setup_group_with_perms(group_name, perm_codenames, app_label='finance', model='financialrecord'):
    """Helper: create a Group and assign Django model permissions to it."""
    group, _ = Group.objects.get_or_create(name=group_name)
    ct = ContentType.objects.get(app_label=app_label, model=model)
    for codename in perm_codenames:
        perm = Permission.objects.get(content_type=ct, codename=codename)
        group.permissions.add(perm)
    return group


class FinanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Admin group: full CRUD
        admin_group = setup_group_with_perms('Admin', [
            'view_financialrecord', 'add_financialrecord',
            'change_financialrecord', 'delete_financialrecord'
        ])
        # Viewer group: read-only on dashboard, NO finance record access
        viewer_group, _ = Group.objects.get_or_create(name='Viewer')

        self.admin = User.objects.create_user(username='admin', password='password123')
        self.admin.groups.set([admin_group])

        self.viewer = User.objects.create_user(username='viewer', password='password123')
        self.viewer.groups.set([viewer_group])

    def test_create_record(self):
        """Admin with add_financialrecord perm can create records."""
        self.client.force_authenticate(user=self.admin)
        data = {
            "amount": "100.50",
            "type": "Income",
            "category": "Salary",
            "date": datetime.date.today().isoformat(),
            "notes": "Test income"
        }
        res = self.client.post('/api/finance/records/', data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FinancialRecord.objects.count(), 1)

    def test_soft_delete(self):
        """Admin can soft-delete a record."""
        record = FinancialRecord.objects.create(
            user=self.admin, amount=Decimal("50.00"), type="Expense", category="Food", date=datetime.date.today()
        )
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(f'/api/finance/records/{record.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        record.refresh_from_db()
        self.assertTrue(record.is_deleted)

    def test_viewer_access_denied(self):
        """Viewer (no finance record permissions) should be blocked from finance records."""
        FinancialRecord.objects.create(
            user=self.admin, amount=Decimal("1000.00"), type="Income", category="Business", date=datetime.date.today()
        )
        self.client.force_authenticate(user=self.viewer)
        res = self.client.get('/api/finance/records/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
