from django.urls import path, include

urlpatterns = [
    path("", include("tangled_django.explorer.urls")),
]
