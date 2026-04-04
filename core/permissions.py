from rest_framework.permissions import BasePermission


def _is_admin(user):
    """True if the user is a superuser OR belongs to the 'Admin' group."""
    return user.is_superuser or user.groups.filter(name='Admin').exists()


class DenyInactive(BasePermission):
    """Block any inactive user."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsAdminRole(BasePermission):
    """Allow access only to superusers or users assigned to the 'Admin' group."""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            _is_admin(request.user)
        )


class FinanceRecordPermission(BasePermission):
    """
    Dynamic permission check for FinancialRecord endpoints.

    - Admins (superuser or 'Admin' group) always get full CRUD access.
    - Other groups/users are checked against standard Django model permissions:
        view_financialrecord  → GET / list / retrieve
        add_financialrecord   → POST
        change_financialrecord→ PUT / PATCH
        delete_financialrecord→ DELETE (soft)

    Grant permissions to a Group via Django admin (Auth > Groups) or the
    Roles API to give that group the relevant access level.
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Admins always have full access
        if _is_admin(request.user):
            return True
        if request.method in self.SAFE_METHODS:
            return request.user.has_perm('finance.view_financialrecord')
        if request.method == 'POST':
            return request.user.has_perm('finance.add_financialrecord')
        if request.method in ('PUT', 'PATCH'):
            return request.user.has_perm('finance.change_financialrecord')
        if request.method == 'DELETE':
            return request.user.has_perm('finance.delete_financialrecord')
        return False


class DashboardPermission(BasePermission):
    """
    Allow access to dashboard endpoints.

    - Admins (superuser or 'Admin' group) always have access.
    - Others need the 'finance.view_financialrecord' permission granted to
      their group via the Roles API or Django admin.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if _is_admin(request.user):
            return True
        return request.user.has_perm('finance.view_financialrecord')
