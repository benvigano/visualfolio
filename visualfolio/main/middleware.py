from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth import get_user_model
    

class ThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.theme = request.COOKIES.get('theme', settings.DEFAULT_THEME)
        return self.get_response(request)
