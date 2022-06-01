from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
urlpatterns = [
    path(r"", include(("PDF_extractor.urls", "PDF_extractor"), namespace="api")),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path(
        "docs/",
        SpectacularSwaggerView.as_view(
            template_name="swagger-ui.html", url_name="schema"
        ),
        name="swagger-ui",
    ),
]
