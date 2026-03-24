"""
URL configuration for your project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings             # YENİ: Ayarları içeri aktardık
from django.conf.urls.static import static   # YENİ: Statik/Medya dosyaları için fonksiyon
from django.views.generic.base import RedirectView

urlpatterns = [
    # mysite_/urls.py içinde:
    path('', include('polls.urls')),  # Baştaki 'polls/' kısmını sildik!
    path('admin/', admin.site.urls), 
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'polls/favicon.png')),
    path('i18n/', include('django.conf.urls.i18n')),
]

# YENİ EKLENEN KISIM: Yüklenen resimlerin geliştirme sunucusunda gösterilebilmesi için gerekli ayar
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)