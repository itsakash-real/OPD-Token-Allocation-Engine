from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DoctorViewSet, SlotViewSet, PatientViewSet,
    TokenViewSet, ReportViewSet, WaitingListViewSet
)

router = DefaultRouter()
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'slots', SlotViewSet, basename='slot')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'tokens', TokenViewSet, basename='token')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'waiting-list', WaitingListViewSet, basename='waiting-list')

urlpatterns = [
    path('', include(router.urls)),
]
