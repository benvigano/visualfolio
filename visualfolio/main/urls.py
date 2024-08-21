from django.urls import path
from .views import (
    DemoLoginView,
)

urlpatterns = [
    path('demo-login/', DemoLoginView.as_view(), name='demo_login')
]
