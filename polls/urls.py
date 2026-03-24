from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    # --- ANA SAYFALAR ---
    path('', views.HomeView.as_view(), name='home'),             # 127.0.0.1:8000/ anasayfa
    path('list/', views.IndexView.as_view(), name='index'),      # Tüm anketlerin listesi

    # --- ANKET DETAY VE OYLAMA ---
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('<int:question_id>/vote/', views.vote, name='vote'),
    
    # --- YAPAY ZEKA ---
    path('<int:question_id>/ai-analyze/', views.ai_analyze_poll, name='ai_analyze'),
    path('ai-draft/', views.ai_draft_poll, name='ai_draft_poll'),

    # --- KULLANICI İŞLEMLERİ ---
    path('login/', views.giris_yap, name='login'),
    path('register/', views.kayit_ol, name='register'),
    path('logout/', views.cikis_yap, name='logout'),
    path('settings/', views.hesap_ayarlari, name='settings'),
    
    # --- OLUŞTURMA VE YÖNETİM ---
    path('create/', views.create_poll, name='create'),
    path('my-polls/', views.MyPollsView.as_view(), name='my_polls'),
    path('<int:question_id>/download-pdf/', views.download_pdf, name='download_pdf'),
    
    # --- MARKET ---
    path('buy-membership/<str:plan>/', views.buy_membership, name='buy_membership'),
]