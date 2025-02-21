from django.urls import path
from .views import (
    LoginView,
    HomeView,
    AssetsView,
    AccountsView,
    EarningsView,
    TransactionsView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('home/', HomeView.as_view(), name='home'),
    path('assets/', AssetsView.as_view(), name='assets'),
    path('accounts/', AccountsView.as_view(), name='accounts'),
    path('earnings/', EarningsView.as_view(), name='earnings'),
    path('transactions/', TransactionsView.as_view(), name='transactions')
]
