from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from django.contrib.auth import views as auth_views

app_name = 'account'

urlpatterns = [
    path('signup', views.signup.as_view()),
    path('api/token', obtain_auth_token, name="obtain-token"),
    path('api/change-password/', views.changePasswordView.as_view(), name='change-password'),
    path('login', views.loginView.as_view()),
    path('login/token', views.loginTokenView.as_view()),
    path('logout', views.logoutView.as_view()),
    path('deleteAccount', views.deleteAccount.as_view()),
    path('request-reset-email/', views.RequestPasswordResetEmail.as_view()),
    path('password-reset/<uidb64>/<token>/', views.PasswordTokenCheckAPI.as_view()),
]