from django.urls import path
from .views import (
    LoginView,
    OverviewView,
    AssetsView,
    AccountsView,
    EarningsView,
    TransactionsView,
    RegistrationView,
    LogoutView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('overview/', OverviewView.as_view(), name='overview'),
    path('assets/', AssetsView.as_view(), name='assets'),
    path('accounts/', AccountsView.as_view(), name='accounts'),
    path('earnings/', EarningsView.as_view(), name='earnings'),
    path('transactions/', TransactionsView.as_view(), name='transactions')
]
