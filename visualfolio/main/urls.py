from django.urls import path
from .views import (
    DemoLoginView,
    HomeView,
    AssetsView,
    AccountsView,
    EarningsView,
    TransactionsView,
    DemoInitializingView,
    DemoInitProgressView
)

urlpatterns = [
    path('demo-login/', DemoLoginView.as_view(), name='demo_login'),
    path('home/', HomeView.as_view(), name='home'),
    path('initializing/', DemoInitializingView.as_view(), name='demo_initializing'),
    path('init-progress/', DemoInitProgressView.as_view(), name='demo_init_progress'),
    path('assets/', AssetsView.as_view(), name='assets'),
    path('accounts/', AccountsView.as_view(), name='accounts'),
    path('earnings/', EarningsView.as_view(), name='earnings'),
    path('transactions/', TransactionsView.as_view(), name='transactions')
]
