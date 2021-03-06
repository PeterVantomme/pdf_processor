from django.urls import path
from rest_framework import routers
from .views import PDF_Extract_ViewSet, QR_ViewSet, Userview, ChangePasswordView, RegisterView, CleanupView, OCR_ViewSet
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView)

router = routers.DefaultRouter()
router.register(r'extract', PDF_Extract_ViewSet, basename="extract")
router.register(r'qr', QR_ViewSet, basename="qr")

# Wire up our API using automatic URL routing.
urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', Userview.as_view(), name='user'),
    path('user/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('qr/<str:filename>', QR_ViewSet.as_view({'get': 'get_file'}), name='qr_file'),
    path('extract/<str:documenttype>', PDF_Extract_ViewSet.as_view({'post': 'extract_data'}), name='extract_data'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('qr/', QR_ViewSet.as_view({'post': 'create'}), name='qr_create'),
    path('ocr/', OCR_ViewSet.as_view({'post': 'convert_to_text'}), name='ocr_convert'),
    path('cleanup/', CleanupView.as_view({'delete': 'cleanup'}), name='cleanup'),
]