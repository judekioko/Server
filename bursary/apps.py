from django.apps import AppConfig


class BursaryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bursary'
    
    def ready(self):
        # Import background task manager
        try:
            from . import background_tasks
            # Initialize background task manager
            background_tasks.initialize()
        except ImportError:
            pass