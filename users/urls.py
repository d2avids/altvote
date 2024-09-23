from django.urls import path, re_path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import LoginPage, GoogleLogin, GoogleLoginCallback, ProtectedView

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login', LoginPage.as_view(), name='login'),
    re_path(r'^api/v1/auth/accounts/', include('allauth.urls')),
    path('api/v1/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/v1/auth/', include('dj_rest_auth.urls')),
    path('api/v1/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/v1/auth/google/callback/', GoogleLoginCallback.as_view(), name='google_login_callback',),
    path('api/v1/check_auth/', ProtectedView.as_view(), name='protected_view')
]
