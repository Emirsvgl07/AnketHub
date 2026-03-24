from django.contrib import admin
from django.utils.html import mark_safe
from .models import Choice, Question

# --- ADMIN PANELİ BAŞLIKLARINI ÖZELLEŞTİRME ---
admin.site.site_header = "AnketHub Yönetim Paneli"
admin.site.site_title = "AnketHub Admin Portalı"
admin.site.index_title = "AnketHub Kontrol Üssüne Hoş Geldiniz"

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3 # Yeni anket eklerken 3 boş şık alanı açar

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # Listede görünecek sütunlar
    list_display = ('question_text', 'author', 'is_approved', 'is_private', 'pub_date', 'image_preview')
    
    # Listeden çıkmadan tek tıkla onay kutucuğunu değiştirebilme
    list_editable = ('is_approved',)
    
    # Sağ taraftaki filtreleme menüsü
    list_filter = ['pub_date', 'is_approved', 'is_private', 'author']
    
    # Soru metni içinde arama yapma
    search_fields = ['question_text']
    
    # Anket düzenleme sayfasında şıkları da alt alta gösterir
    inlines = [ChoiceInline]
    
    # Düzenleme sayfasında resmin büyük halini "sadece okunabilir" olarak göster
    readonly_fields = ('image_preview_large',)

    # --- TOPLU İŞLEMLER (ACTIONS) ---
    actions = ['toplu_onayla', 'toplu_onay_kaldir']

    @admin.action(description='Seçili anketleri tek tıkla ONAYLA ✅')
    def toplu_onayla(self, request, queryset):
        rows_updated = queryset.update(is_approved=True)
        self.message_user(request, f"{rows_updated} adet anket başarıyla onaylandı.")

    @admin.action(description='Seçili anketlerin onayını KALDIR ❌')
    def toplu_onay_kaldir(self, request, queryset):
        rows_updated = queryset.update(is_approved=False)
        self.message_user(request, f"{rows_updated} adet anketin onayı kaldırıldı.")

    # --- GÖRSEL ÖNİZLEME FONKSİYONLARI ---
    
    def image_preview(self, obj):
        """Ana listedeki küçük resim önizlemesi"""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 60px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" />')
        return mark_safe('<span style="color: #999; font-style: italic;">Görsel Yok</span>')
    image_preview.short_description = 'Küçük Resim'

    def image_preview_large(self, obj):
        """Anket detay sayfasındaki büyük resim önizlemesi"""
        if obj.image:
            return mark_safe(f'''
                <div style="margin-bottom: 10px;">
                    <img src="{obj.image.url}" style="max-height: 300px; border-radius: 15px; border: 3px solid #f1f1f1;" />
                    <p style="margin-top: 5px; color: #666; font-size: 12px;">Mevcut dosya yolu: {obj.image.name}</p>
                </div>
            ''')
        return "Henüz bir görsel yüklenmemiş."
    image_preview_large.short_description = 'Anket Görseli Detayı'