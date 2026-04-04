from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status

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
