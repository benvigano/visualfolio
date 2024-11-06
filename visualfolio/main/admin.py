from django.apps import apps
from django.contrib import admin

app_models = apps.get_app_config('main').get_models()

for model in app_models:
    admin.site.register(model)
