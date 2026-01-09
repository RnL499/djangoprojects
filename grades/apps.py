from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grades'
    # app label should match folder/name
    # label removed to use default 'grades'
