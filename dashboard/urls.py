from django.urls import path
from .views import SummaryView, TrendsView

urlpatterns = [
    path('summary/', SummaryView.as_view(), name='dashboard-summary'),
    path('trends/', TrendsView.as_view(), name='dashboard-trends'),
]
