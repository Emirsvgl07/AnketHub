import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User 
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse # EKSİKTİ, EKLENDİ (Sayfa çökmesini önler)
from django.utils.translation import gettext_lazy as _ # ÇOKLU DİL DESTEĞİ İÇİN EKLENDİ

class Question(models.Model):
    # Çoklu dil desteği için metinler _("...") içine alındı
    question_text = models.CharField(_("soru metni"), max_length=200)
    pub_date = models.DateTimeField(_("yayınlanma tarihi"))
    
    # Anketin bitiş tarihi (2. Madde için gerekli)
    end_date = models.DateTimeField(_("bitiş tarihi"), null=True, blank=True)
    
    # Grup / Gizli Anket özelliği (Sadece linki olanlar görebilir)
    is_private = models.BooleanField(_("gizli mi?"), default=False)
    
    # Anketin sahibi ve onay durumu
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("yazar"))
    is_approved = models.BooleanField(_("onaylandı mı?"), default=False)

    # Resim yükleme alanı
    image = models.ImageField(_("resim"), upload_to='question_images/', blank=True, null=True)

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    
    def total_votes(self):
        return sum(choice.votes for choice in self.choice_set.all())

    # Anketin süresi dolmuş mu kontrol eden özellik
    @property
    def is_active(self):
        if self.end_date:
            return timezone.now() <= self.end_date
        return True # Bitiş tarihi girilmediyse hep aktiftir

    def get_absolute_url(self):
        """Bu anketin detay sayfasının adresini döndürür."""
        return reverse('polls:detail', args=[str(self.id)])

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(_("seçenek metni"), max_length=200)
    votes = models.IntegerField(_("oylar"), default=0)

    def __str__(self):
        return self.choice_text


# --- 3. MADDE: KİMİN OY VERDİĞİNİ TUTAN MODEL ---
class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        # Bir kullanıcı aynı ankete sadece 1 kayıt girebilir.
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.username} -> {self.question.question_text}"


# --- 4. MADDE: KULLANICI PROFİLİ VE PUAN SİSTEMİ ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0) # Herkes 0 puanla başlar

    # VİTRİN DEĞİŞİKLİĞİ: Marketten alınan özel rozeti veritabanında tutmamız ŞART.
    badge = models.CharField(max_length=50, blank=True, null=True)

    # DİNAMİK ROZET: Kullanıcının özel rozeti yoksa puanına göre otomatik unvan verir
    @property
    def dinamik_seviye(self):
        if self.badge: # Marketten "Premium" falan aldıysa onu göster
            return self.badge
            
        # Almadıysa puanına göre çevrilebilir (i18n) dinamik seviye ver
        if self.points < 50:
            return _("🌱 Çaylak")
        elif self.points < 200:
            return _("✍️ Anketör")
        elif self.points < 500:
            return _("🔍 Analist")
        else:
            return _("👑 Üstat")

    def __str__(self):
        return f"{self.user.username} Profili - {self.points} Puan"

# Sinyaller: Sisteme yeni bir User kayıt olduğunda, otomatik Profile oluştur.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()