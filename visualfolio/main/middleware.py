from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth import get_user_model


class DemoUserExistenceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If settings.MODE is set to 'demo' AND the user is authenticated
        if getattr(settings, 'MODE', 'production') == 'demo' and request.user.is_authenticated:
            User = get_user_model()
            # If the user doesn't exist (because it was deleted by the demo user cleanup automation)
            if not User.objects.filter(id=request.user.id).exists():
                # Log out the user and redirect to login
                logout(request)
                return redirect('login')

        response = self.get_response(request)
        return response
    

class ThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.theme = request.COOKIES.get('theme', settings.DEFAULT_THEME)
        return self.get_response(request)
