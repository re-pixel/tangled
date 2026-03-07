"""
WSGI config for Tangled Graph Explorer Django project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tangled_django.settings")

application = get_wsgi_application()
