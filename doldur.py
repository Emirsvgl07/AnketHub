import os
import django
import random
import datetime

# 1. Django Ayarlarını Tanıtıyoruz
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite_.settings') 
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from polls.models import Question, Choice

def doldur():
    print("🚀 Veritabanı 30 örnek anketle dolduruluyor...\n")

    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("HATA: Önce admin hesabı oluşturmalısın!")
        return

    test_user, created = User.objects.get_or_create(username="anket_canavari", defaults={"email": "test@ankethub.com"})
    
    now = timezone.now()

    # SENİN MEVCUT ÖZEL ANKETLERİN
    ornek_anketler = [
        {
            "soru": "Sizce yazılım dünyasında 2026'nın en popüler dili hangisi olacak?",
            "yazar": admin_user, "gizli_mi": False,
            "secenekler": [("Python", 125), ("JavaScript", 85), ("Rust", 45), ("C#", 60)]
        },
        {
            "soru": "İmza parfümünüz olarak hangisini tercih ederdiniz?",
            "yazar": test_user, "gizli_mi": False,
            "secenekler": [("Dior Sauvage Elixir", 65), ("Jean Paul Gaultier Le Male Elixir", 45), ("Bleu de Chanel EDP", 55), ("Versace Eros", 30)]
        },
        {
            "soru": "Fiyat/Performans açısından en mantıklı mekanik klavye seçimi hangisi?",
            "yazar": test_user, "gizli_mi": False,
            "secenekler": [("Ajazz AK680 Max", 80), ("Razer BlackWidow", 40), ("Logitech G Pro", 35), ("SteelSeries Apex", 25)]
        },
        {
            "soru": "Sivas Cumhuriyet Üniversitesi Bilişim Sistemleri vizeleri ne kadar zorluyor?",
            "yazar": test_user, "gizli_mi": True,
            "secenekler": [("Çok zorluyor, sabahlıyoruz", 40), ("Düzenli çalışana kolay", 15), ("Henüz başlamadım :)", 25)]
        }
    ]

    # 30'A TAMAMLAMAK İÇİN EKSTRA UYDURMA SORULAR
    uydurma_sorular = [
        ["Hangi işletim sistemini tercih ediyorsunuz?", ["Windows", "MacOS", "Linux", "Android"]],
        ["Yapay zeka işimizi elimizden alacak mı?", ["Evet", "Hayır", "Kısmen"]],
        ["En iyi oyun türü hangisidir?", ["FPS", "RPG", "Strateji", "Spor"]],
        ["Kahvaltının vazgeçilmezi nedir?", ["Zeytin", "Peynir", "Yumurta", "Nutella"]],
        ["Antalya'nın en güzel plajı neresi?", ["Konyaaltı", "Lara", "Kaputaş", "Olympos"]],
        ["Hangi müzik türünü dinlersiniz?", ["Pop", "Rock", "Rap", "Klasik"]],
        ["Yaz tatili mi kış tatili mi?", ["Yaz", "Kış"]],
        ["Uzaktan eğitim mi yüz yüze mi?", ["Uzaktan", "Yüz yüze", "Hibrit"]],
        ["En sevdiğiniz sosyal medya?", ["Instagram", "Twitter", "YouTube", "TikTok"]],
        ["Birinci el mi ikinci el mi?", ["Sıfır", "İkinci El"]],
        ["Gece kuşu mu sabahçı mı?", ["Gece", "Sabah"]],
        ["Hangi Fast Food daha iyi?", ["Burger", "Pizza", "Döner", "Tavuk"]],
        ["En iyi dizi hangisi?", ["Breaking Bad", "Dark", "The Office", "Kurtlar Vadisi"]],
        ["Hangi browser daha hızlı?", ["Chrome", "Brave", "Safari", "Firefox"]],
        ["Geleceğin mesleği nedir?", ["Yazılımcı", "Veri Analisti", "Çiftçi"]],
        ["En iyi telefon markası?", ["Apple", "Samsung", "Xiaomi"]],
        ["Spor yapıyor musunuz?", ["Evet", "Hayır", "Pazartesi başlayacağım"]],
        ["Çay mı kahve mi?", ["Çay", "Kahve"]],
        ["En sevdiğiniz meyve?", ["Elma", "Muz", "Çilek"]],
        ["Klavye mi Mouse mu?", ["Klavye", "Mouse"]],
        ["Bitcoin yükselir mi?", ["Yükselir", "Düşer", "Stabil kalır"]],
        ["En iyi araba markası?", ["BMW", "Mercedes", "Audi", "Tesla"]],
        ["Hangi süper güç?", ["Uçmak", "Görünmezlik", "Işınlanma"]],
        ["En sevdiğiniz renk?", ["Mavi", "Kırmızı", "Siyah"]],
        ["Hangi takım şampiyon olur?", ["FB", "GS", "BJK", "TS"]],
        ["En iyi içecek?", ["Su", "Kola", "Ayran"]]
    ]

    # Mevcut anketleri ekle
    for anket in ornek_anketler:
        q, created = Question.objects.get_or_create(
            question_text=anket["soru"],
            defaults={
                "pub_date": now - datetime.timedelta(days=random.randint(1, 4)),
                "author": anket["yazar"],
                "is_approved": True,
                "is_private": anket["gizli_mi"]
            }
        )
        if created:
            for secenek, oy in anket["secenekler"]:
                Choice.objects.create(question=q, choice_text=secenek, votes=oy)
            print(f"✅ Özel Anket Eklendi: {q.question_text}")

    # Uydurma anketleri ekle (30'a tamamla)
    for soru, secenekler in uydurma_sorular:
        q, created = Question.objects.get_or_create(
            question_text=soru,
            defaults={
                "pub_date": now - datetime.timedelta(days=random.randint(5, 10)),
                "author": admin_user,
                "is_approved": True,
                "is_private": False
            }
        )
        if created:
            for s in secenekler:
                Choice.objects.create(question=q, choice_text=s, votes=random.randint(10, 200))
            print(f"📦 Uydurma Anket Eklendi: {q.question_text}")

    print("\n🎉 Toplamda 30 civarı anketle veritabanın şenlendi!")

if __name__ == '__main__':
    doldur()