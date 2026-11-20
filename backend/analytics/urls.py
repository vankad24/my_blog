from django.urls import path

from .views import SiteVisitView

app_name = 'analytics'

urlpatterns = [
    path('visits/', SiteVisitView.as_view(), name='site-visits'),
]
