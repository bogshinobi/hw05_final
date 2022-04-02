import django.contrib.auth.views as av
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        av.LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path(
        'login/',
        av.LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_change/done/',
        av.PasswordChangeDoneView.
        as_view(template_name='users/password_change_done.html'),
        name='password_change_done'
    ),
    path(
        'password_change/',
        av.PasswordChangeView.
        as_view(template_name='users/password_change_form.html'),
        name='password_change_form'
    ),
    path(
        'password_reset/done/',
        av.PasswordResetDoneView.
        as_view(template_name='users/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'password_reset/',
        av.PasswordResetView.
        as_view(template_name='users/password_reset_form.html'),
        name='password_reset_form'
    ),
    path(
        'reset/<uidb64>/<token>',
        av.PasswordResetConfirmView.
        as_view(template_name='users/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        av.PasswordResetCompleteView.
        as_view(template_name='users/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]
