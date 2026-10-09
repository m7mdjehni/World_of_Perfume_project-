from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication & Security: built-in login/logout/password views,
    # plus a token endpoint for API clients (mobile apps, scripts, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),

    path('', include('store.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
