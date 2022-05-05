from django.urls import path, include
from rest_framework import routers
from .views import UploadViewSet, Userview
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView)

router = routers.DefaultRouter()
router.register(r'upload', UploadViewSet, basename="upload")

# Wire up our API using automatic URL routing.
urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', Userview.as_view(), name='user'),
]