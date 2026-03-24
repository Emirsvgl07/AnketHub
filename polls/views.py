import os
import json
import re
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.http import HttpResponseRedirect, JsonResponse 
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db.models import Q 
from django.contrib.auth.models import User
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from xhtml2pdf.default import DEFAULT_FONT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

import google.generativeai as genai 
from .models import Choice, Question, Vote 
from .forms import ExtendedUserCreationForm # YENİ EKLENDİ

# --- AI AYARLARI ---
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

# --- GENEL GÖRÜNÜMLER ---

class HomeView(generic.TemplateView):
    template_name = "polls/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mevcut_uye = User.objects.count()
        context['kalan_kontenjan'] = max(0, 500 - mevcut_uye)
        context['toplam_uye'] = mevcut_uye
        
        try:
            context['top_users'] = User.objects.select_related('profile').order_by('-profile__points')[:10]
        except:
            context['top_users'] = [] 
            
        return context

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        qs = Question.objects.filter(
            pub_date__lte=timezone.now(), 
            is_approved=True,
            is_private=False
        ).order_by("-pub_date")

        tab = self.request.GET.get('tab', 'all')
        if tab == 'official':
            qs = qs.filter(author__is_superuser=True) 
        elif tab == 'community':
            qs = qs.exclude(author__is_superuser=True) 
        elif tab == 'popular': 
            qs = qs.order_by("?")[:10] 
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context['current_tab'] = self.request.GET.get('tab', 'all')
        all_polls = Question.objects.filter(is_approved=True, is_private=False)
        context['total_count'] = all_polls.count()
        active_count = all_polls.filter(Q(end_date__isnull=True) | Q(end_date__gte=now)).count()
        context['active_count'] = active_count

        if self.request.user.is_authenticated:
            user_votes = Vote.objects.filter(user=self.request.user).values_list('question_id', flat=True)
            context['voted_questions'] = user_votes
            context['solved_count'] = len(user_votes)
            context['unsolved_count'] = active_count - Vote.objects.filter(user=self.request.user, question__is_private=False).count()
        else:
            context['voted_questions'] = []
            
        return context

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"
    
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

# --- ANKET İŞLEMLERİ ---

@login_required 
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if Vote.objects.filter(user=request.user, question=question).exists():
        return render(request, "polls/detail.html", {"question": question, "error_message": "Bu ankete zaten oy verdiniz."})
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(request, "polls/detail.html", {"question": question, "error_message": "Bir seçenek işaretlemediniz."})
    else:
        selected_choice.votes += 1
        selected_choice.save()
        Vote.objects.create(user=request.user, question=question, choice=selected_choice)
        request.user.profile.points += 10
        request.user.profile.save()
        messages.success(request, 'Tebrikler! Anket çözdünüz ve 10 Puan kazandınız. 🪙')
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

@login_required
def create_poll(request):
    REQUIRED_POINTS = 50 
    if request.method == 'POST':
        if request.user.profile.points < REQUIRED_POINTS:
            messages.error(request, f'Anket oluşturmak için {REQUIRED_POINTS} puana ihtiyacınız var. Şu anki puanınız: {request.user.profile.points} 🪙')
            return redirect('polls:create')
        question_text = request.POST.get('question_text')
        choices = request.POST.getlist('choice')
        image = request.FILES.get('image')
        is_private = request.POST.get('is_private') == 'on'
        if question_text and choices:
            question = Question.objects.create(
                question_text=question_text, pub_date=timezone.now(), author=request.user,
                is_approved=False, image=image, is_private=is_private
            )
            for choice_text in choices:
                if choice_text.strip():
                    Choice.objects.create(question=question, choice_text=choice_text)
            request.user.profile.points -= REQUIRED_POINTS
            request.user.profile.save()
            if is_private:
                messages.success(request, f'Gizli Grup Anketiniz onaya gönderildi! ({REQUIRED_POINTS} Puan harcandı) 🕵️‍♂️')
            else:
                messages.success(request, f'Anketiniz onaya gönderildi! ({REQUIRED_POINTS} Puan harcandı) 💸')
            return redirect('polls:my_polls')
    return render(request, 'polls/create_poll.html', {'required_points': REQUIRED_POINTS})

class MyPollsView(LoginRequiredMixin, generic.ListView):
    template_name = 'polls/my_polls.html'
    context_object_name = 'my_polls'
    def get_queryset(self):
        return Question.objects.filter(author=self.request.user).order_by('-pub_date')

# --- YAPAY ZEKA FONKSİYONLARI ---

@login_required
def ai_analyze_poll(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if question.total_votes() == 0:
        return JsonResponse({'status': 'error', 'message': 'Analiz yapabilmek için en az 1 oy kullanılması gerekiyor.'})
    choices_text = "\n".join([f"- {choice.choice_text}: {choice.votes} oy" for choice in question.choice_set.all()])
    prompt = f"""
    Sen profesyonel ve analitik düşünen bir veri danışmanısın. Aşağıdaki anket verilerini incele.
    Sonuçların ne anlama geldiğini, çoğunluğun eğilimini ve genel durumu 3-4 cümlelik kısa, etkileyici ve anlaşılır bir Türkçe özetle yorumla.
    Gereksiz uzatma, sadece doğrudan analiz yap.
    Anket Sorusu: "{question.question_text}"
    Toplam Oy Sayısı: {question.total_votes()}
    Dağılım:
    {choices_text}
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        if response.text:
            return JsonResponse({'status': 'success', 'analysis': response.text})
        else:
            return JsonResponse({'status': 'error', 'message': 'AI yanıt döndüremedi.'})
    except Exception as e:
        try:
            secilen = next(m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods)
            model = genai.GenerativeModel(secilen)
            response = model.generate_content(prompt)
            return JsonResponse({'status': 'success', 'analysis': response.text})
        except:
            return JsonResponse({'status': 'error', 'message': f'Detaylı Hata: {str(e)}'})

@login_required
def ai_draft_poll(request):
    konu = request.GET.get('topic', '')
    if not konu:
        return JsonResponse({'error': 'Lütfen bir konu girin.'}, status=400)
    prompt = f"""
    Sen yaratıcı bir anket tasarımcısısın. Kullanıcı şu konuyu verdi: "{konu}".
    Bu konuyla ilgili insanların dikkatini çekecek bir anket sorusu ve tam olarak 4 adet mantıklı, birbirinden farklı şık üret.
    LÜTFEN SADECE VE SADECE AŞAĞIDAKİ JSON FORMATINDA YANIT VER, BAŞKA HİÇBİR AÇIKLAMA YAZMA:
    {{"soru": "Ürettiğin Soru Metni", "siklar": ["Şık 1", "Şık 2", "Şık 3", "Şık 4"]}}
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        try:
            clean_json = re.search(r'\{.*\}', response.text, re.DOTALL).group()
            data = json.loads(clean_json)
            return JsonResponse(data)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Yapay zeka veriyi JSON formatında döndüremedi.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'AI Bağlantı Hatası: {str(e)}'}, status=500)

# --- KULLANICI & HESAP İŞLEMLERİ ---

def giris_yap(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Tekrar hoş geldin, {user.username}! 👋')
            return redirect('polls:home')
    else:
        form = AuthenticationForm()
    return render(request, 'polls/login.html', {'form': form})

# GÜNCELLENEN KAYIT OLMA FONKSİYONU
def kayit_ol(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            toplam_uye = User.objects.count()
            if toplam_uye <= 500:
                user.profile.points += 300
                user.profile.save()
                messages.success(request, f'Aramıza hoş geldin {user.first_name}! İlk 500 üyeden biri olduğun için 300 Puan kazandın! 🎁')
            else:
                messages.info(request, f'Hoş geldin {user.first_name}! Anket çözerek puan kazanmaya başlayabilirsin.')
            login(request, user)
            return redirect('polls:home')
    else:
        form = ExtendedUserCreationForm()
    return render(request, 'polls/register.html', {'form': form})

def cikis_yap(request):
    logout(request)
    messages.info(request, 'Başarıyla çıkış yaptın. Görüşmek üzere! 👋')
    return redirect('polls:home')

@login_required
def hesap_ayarlari(request):
    if request.method == 'POST':
        u = request.user
        u.first_name = request.POST.get('first_name', '')
        u.last_name = request.POST.get('last_name', '')
        u.email = request.POST.get('email', '')
        u.save()
        messages.success(request, 'Profil bilgilerin başarıyla güncellendi! ✅')
        return redirect('polls:settings')
    context = {
        'solved_count': Vote.objects.filter(user=request.user).count(),
        'created_count': Question.objects.filter(author=request.user).count()
    }
    return render(request, 'polls/settings.html', context)

# YENİ: ÜYELİK SATIN ALMA FONKSİYONU
@login_required
def buy_membership(request, plan):
    profile = request.user.profile
    plans = {
        'premium': {'cost': 500, 'name': 'Premium Anketör', 'badge': '🌟 Premium'},
        'legend': {'cost': 2000, 'name': 'Efsanevi Üstat', 'badge': '👑 Üstat'}
    }

    selected_plan = plans.get(plan)
    if not selected_plan:
        return redirect('polls:home')

    if profile.points >= selected_plan['cost']:
        profile.points -= selected_plan['cost']
        profile.badge = selected_plan['badge'] # Profile modelinde badge alanın olduğunu varsayıyorum
        profile.save()
        messages.success(request, f'Tebrikler! Artık bir {selected_plan["name"]} üyesiniz! {selected_plan["badge"]}')
    else:
        messages.error(request, f'Yetersiz puan! {selected_plan["name"]} için {selected_plan["cost"]} 🪙 gerekiyor.')

    return redirect('polls:home')


# --- KESİN ÇÖZÜM PDF OLUŞTURMA FONKSİYONU ---
@login_required
def download_pdf(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    template_path = 'polls/pdf_template.html' 
    
    font_path = os.path.join(settings.BASE_DIR, 'ARIAL.TTF')
    
    try:
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        addMapping('Arial', 0, 0, 'Arial') 
        addMapping('Arial', 0, 1, 'Arial') 
        addMapping('Arial', 1, 0, 'Arial') 
        addMapping('Arial', 1, 1, 'Arial') 
        DEFAULT_FONT['helvetica'] = 'Arial'
        DEFAULT_FONT['sans-serif'] = 'Arial'
        DEFAULT_FONT['arial'] = 'Arial'
    except Exception as e:
        print("Font yükleme hatası:", e)
    
    context = {'question': question}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="anket_sonucu_{question.id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response, encoding='utf-8')
    
    if pisa_status.err:
        return HttpResponse('PDF oluşturulurken bir hata oluştu.')
    return response
