from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from finance.models import FinancialRecord

User = get_user_model()


class CustomUserTests(TestCase):
    """Tests for the CustomUser model and the User API endpoints."""

    def setUp(self):
        self.client = APIClient()

        admin_group, _ = Group.objects.get_or_create(name='Admin')
        viewer_group, _ = Group.objects.get_or_create(name='Viewer')

        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123',
        )
        self.admin_user.groups.set([admin_group])

        self.viewer_user = User.objects.create_user(
            username='viewer_test',
            email='viewer@test.com',
            password='password123',
        )
        self.viewer_user.groups.set([viewer_group])

    def test_user_role_property(self):
        """Role property should return the group name."""
        self.assertEqual(self.viewer_user.role, 'Viewer')
        self.assertEqual(str(self.viewer_user), 'viewer_test - Viewer')
        self.assertEqual(str(self.admin_user), 'admin_test - Admin')

    def test_register_endpoint(self):
        """Registration endpoint creates a user and assigns the correct group."""
        url = '/api/users/register/'
        data = {
            'username': 'new_user',
            'password': 'strongpassword',
            'email': 'new@test.com',
            'set_role': 'Analyst'
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='new_user')
        self.assertEqual(user.role, 'Analyst')

    def test_admin_crud_access(self):
        """Admin can access the full User CRUD API."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get('/api/users/admin/users/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data['results']), 2)

    def test_viewer_crud_access_denied(self):
        """Non-Admin cannot access the User CRUD API."""
        self.client.force_authenticate(user=self.viewer_user)
        res = self.client.get('/api/users/admin/users/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_deactivate_user(self):
        """Admin can set is_active=False on a user via PATCH."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.patch(
            f'/api/users/admin/users/{self.viewer_user.id}/',
            {'is_active': False},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.viewer_user.refresh_from_db()
        self.assertFalse(self.viewer_user.is_active)

    def test_admin_can_change_user_role(self):
        """Admin can change a user's group (role) via PATCH."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.patch(
            f'/api/users/admin/users/{self.viewer_user.id}/',
            {'set_role': 'Analyst'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.viewer_user.refresh_from_db()
        self.assertEqual(self.viewer_user.role, 'Analyst')


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
