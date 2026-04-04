from rest_framework import viewsets, generics, permissions
from .models import CustomUser
from .serializers import UserSerializer, UserUpdateSerializer
from core.permissions import IsAdminRole


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for user management.
    Only users in the 'Admin' group can access these endpoints.
    Admins can activate/deactivate users and change their group (role).
    """
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
