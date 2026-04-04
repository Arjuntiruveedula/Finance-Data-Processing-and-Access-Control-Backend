from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from finance.models import FinancialRecord

User = get_user_model()


class RolesAPITests(TestCase):
    """Tests for the dynamic Roles & Permissions management API."""

    def setUp(self):
        self.client = APIClient()

        # Admin user assigned to 'Admin' group
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        self.admin = User.objects.create_superuser(username='admin', password='123')
        self.admin.groups.set([admin_group])

        # Non-admin user
        viewer_group, _ = Group.objects.get_or_create(name='Viewer')
        self.viewer = User.objects.create_user(username='viewer', password='123')
        self.viewer.groups.set([viewer_group])

        # A sample permission to use in tests
        ct = ContentType.objects.get(app_label='finance', model='financialrecord')
        self.view_perm = Permission.objects.get(content_type=ct, codename='view_financialrecord')
        self.add_perm = Permission.objects.get(content_type=ct, codename='add_financialrecord')

    # --- Role CRUD ---

    def test_admin_can_list_roles(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/roles/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_list_roles(self):
        self.client.force_authenticate(user=self.viewer)
        res = self.client.get('/api/roles/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_role(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/roles/', {'name': 'Auditor'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Group.objects.filter(name='Auditor').exists())

    def test_admin_can_rename_role(self):
        group = Group.objects.create(name='OldName')
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(f'/api/roles/{group.id}/', {'name': 'NewName'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        group.refresh_from_db()
        self.assertEqual(group.name, 'NewName')

    def test_admin_can_delete_role(self):
        group = Group.objects.create(name='Temporary')
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(f'/api/roles/{group.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(name='Temporary').exists())

    # --- Permission assignment ---

    def test_admin_can_assign_permissions_to_role(self):
        group = Group.objects.create(name='Analyst')
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            f'/api/roles/{group.id}/permissions/',
            {'permission_ids': [self.view_perm.id]},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(self.view_perm, group.permissions.all())

    def test_admin_can_remove_permissions_from_role(self):
        group = Group.objects.create(name='Analyst')
        group.permissions.add(self.view_perm, self.add_perm)
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(
            f'/api/roles/{group.id}/permissions/remove/',
            {'permission_ids': [self.add_perm.id]},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.add_perm, group.permissions.all())
        self.assertIn(self.view_perm, group.permissions.all())

    def test_invalid_permission_id_rejected(self):
        group = Group.objects.create(name='Test')
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            f'/api/roles/{group.id}/permissions/',
            {'permission_ids': [99999]},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Available permissions list ---

    def test_admin_can_list_available_permissions(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/roles/available-permissions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(len(res.data['results']), 0)
