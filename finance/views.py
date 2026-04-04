from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import FinancialRecord
from .serializers import FinancialRecordSerializer
from core.permissions import FinanceRecordPermission


class FinancialRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD for Financial Records.
    Access is controlled dynamically via Django Group permissions:
      - view_financialrecord  → GET/list/retrieve
      - add_financialrecord   → POST
      - change_financialrecord→ PUT/PATCH
      - delete_financialrecord→ DELETE (soft)

    Grant these permissions to a Group in the Django admin panel to
    give that group the relevant access level.
    """
    serializer_class = FinancialRecordSerializer
    permission_classes = [permissions.IsAuthenticated, FinanceRecordPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['type', 'category', 'date']
    ordering_fields = ['date', 'amount']
    search_fields = ['notes', 'category']

    def get_queryset(self):
        return FinancialRecord.objects.filter(is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        from rest_framework.response import Response
        from rest_framework import status
        return Response(status=status.HTTP_204_NO_CONTENT)
