from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path(r"", include(("PDF_extractor.urls", "PDF_extractor"), namespace="api")),
    
]
