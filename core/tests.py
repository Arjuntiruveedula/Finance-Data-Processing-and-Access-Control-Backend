from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework.test import APIRequestFactory
from core.permissions import IsAdminRole, DenyInactive
from django.contrib.contenttypes.models import ContentType
from finance.models import FinancialRecord

User = get_user_model()


def make_user_in_group(username, password, group_name, is_active=True, is_superuser=False):
    """Helper: create a user and assign them to a named Group."""
    group, _ = Group.objects.get_or_create(name=group_name)
    if is_superuser:
        user = User.objects.create_superuser(username=username, password=password)
    else:
        user = User.objects.create_user(username=username, password=password, is_active=is_active)
    user.groups.set([group])
    return user


class CorePermissionsTests(TestCase):
    """Tests for custom dynamic permissions defined in the core app."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = make_user_in_group('admin', '123', 'Admin', is_superuser=True)
        self.analyst = make_user_in_group('analyst', '123', 'Analyst')
        self.viewer = make_user_in_group('viewer', '123', 'Viewer')
        self.inactive = make_user_in_group('inactive', '123', 'Viewer', is_active=False)

    def get_mock_request(self, user):
        class MockRequest:
            def __init__(self, u):
                self.user = u
        return MockRequest(user)

    def test_is_admin_role_allows_admin(self):
        perm = IsAdminRole()
        self.assertTrue(perm.has_permission(self.get_mock_request(self.admin), None))

    def test_is_admin_role_denies_others(self):
        perm = IsAdminRole()
        self.assertFalse(perm.has_permission(self.get_mock_request(self.analyst), None))
        self.assertFalse(perm.has_permission(self.get_mock_request(self.viewer), None))

    def test_deny_inactive(self):
        perm = DenyInactive()
        self.assertFalse(perm.has_permission(self.get_mock_request(self.inactive), None))
        self.assertTrue(perm.has_permission(self.get_mock_request(self.viewer), None))

    def test_user_role_property(self):
        """Role property should reflect the group name."""
        self.assertEqual(self.admin.role, 'Admin')
        self.assertEqual(self.analyst.role, 'Analyst')
        self.assertEqual(self.viewer.role, 'Viewer')
