from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.http import JsonResponse
import re


def login_view(request):
    error = None

    if 'login_attempts' not in request.session:
        request.session['login_attempts'] = 0
        request.session['login_blocked_until'] = None

    blocked_until = request.session.get('login_blocked_until')
    if blocked_until:
        blocked_until_dt = datetime.fromisoformat(blocked_until)
        now = datetime.now()
        if now < blocked_until_dt:
            qolgan = int((blocked_until_dt - now).total_seconds())
            return render(request, 'accounts/login.html', {
                'error': f"Juda ko'p urinish! {qolgan} soniyadan so'ng qayta urining.",
                'blocked': True
            })
        else:
            request.session['login_attempts'] = 0
            request.session['login_blocked_until'] = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        blocked_until = request.session.get('login_blocked_until')
        if blocked_until:
            blocked_until_dt = datetime.fromisoformat(blocked_until)
            now = datetime.now()
            if now < blocked_until_dt:
                qolgan = int((blocked_until_dt - now).total_seconds())
                return render(request, 'accounts/login.html', {
                    'error': f"Juda ko'p urinish! {qolgan} soniyadan so'ng qayta urining.",
                    'blocked': True
                })

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            request.session['login_attempts'] = 0
            request.session['login_blocked_until'] = None
            login(request, user)
            return redirect('dashboard')
        else:
            request.session['login_attempts'] = request.session.get('login_attempts', 0) + 1
            attempts = request.session['login_attempts']

            if attempts >= 3:
                blocked_until = datetime.now() + timedelta(seconds=30)
                request.session['login_blocked_until'] = blocked_until.isoformat()
                request.session['login_attempts'] = 0
                return render(request, 'accounts/login.html', {
                    'error': "3 marta noto'g'ri kiritildi! 30 soniya kuting.",
                    'blocked': True
                })
            else:
                qolgan = 3 - attempts
                error = f"Email yoki parol noto'g'ri! Yana {qolgan} ta urinish qoldi."

    return render(request, 'accounts/login.html', {'error': error})


def logout_view(request):
    logout(request)
    request.session.flush()
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def dashboard(request):
    from hisobotlar.models import PDFHisobot, ImtihonNatija
    from tahlil.models import ExcelJadval, ExcelQator

    # Tanlangan jadvallar
    tanlangan_ids = request.GET.getlist('jadval_ids')

    # Barcha jadvallar (tanlash uchun)
    barcha_jadvallar = ExcelJadval.objects.filter(
        yuklagan_user=request.user
    ).order_by('-yuklangan_vaqt')

    # Statistika hisoblash
    statistika = None
    tanlangan_jadvallar = []

    if tanlangan_ids:
        tanlangan_jadvallar = ExcelJadval.objects.filter(
            pk__in=tanlangan_ids,
            yuklagan_user=request.user
        )

        # Tanlangan jadvallardan statistika
        jami_talabalar = 0
        jami_5 = 0
        jami_4 = 0
        jami_3 = 0
        jami_kelmadi = 0

        for jadval in tanlangan_jadvallar:
            qatorlar = ExcelQator.objects.filter(jadval=jadval)
            ustunlar = jadval.ustunlar

            # Ustun nomlarini topish
            talabalar_ustun = next(
                (u for u in ustunlar if 'talabalar' in u.lower()), None
            )
            besh_ustun = next(
                (u for u in ustunlar if '"5"' in u or u == '5'), None
            )
            tort_ustun = next(
                (u for u in ustunlar if '"4"' in u or u == '4'), None
            )
            uch_ustun = next(
                (u for u in ustunlar if '"3"' in u or u == '3'), None
            )
            kelmadi_ustun = next(
                (u for u in ustunlar if 'kelmadi' in u.lower()), None
            )

            for qator in qatorlar:
                d = qator.qator_data
                try:
                    if talabalar_ustun:
                        jami_talabalar += int(float(d.get(talabalar_ustun, 0) or 0))
                    if besh_ustun:
                        jami_5 += int(float(d.get(besh_ustun, 0) or 0))
                    if tort_ustun:
                        jami_4 += int(float(d.get(tort_ustun, 0) or 0))
                    if uch_ustun:
                        jami_3 += int(float(d.get(uch_ustun, 0) or 0))
                    if kelmadi_ustun:
                        jami_kelmadi += int(float(d.get(kelmadi_ustun, 0) or 0))
                except (ValueError, TypeError):
                    pass

        ozlashtirish = round(
            (jami_5 + jami_4 + jami_3) / jami_talabalar * 100, 1
        ) if jami_talabalar > 0 else 0

        sifat = round(
            (jami_5 + jami_4) / jami_talabalar * 100, 1
        ) if jami_talabalar > 0 else 0

        statistika = {
            'jami_talabalar': jami_talabalar,
            'jami_5': jami_5,
            'jami_4': jami_4,
            'jami_3': jami_3,
            'jami_kelmadi': jami_kelmadi,
            'ozlashtirish': ozlashtirish,
            'sifat': sifat,
        }

    # PDF statistika
    jami_pdf = PDFHisobot.objects.filter(yuklagan_user=request.user).count()
    jami_jadval = barcha_jadvallar.count()

    return render(request, 'accounts/dashboard.html', {
        'jami_pdf': jami_pdf,
        'jami_jadval': jami_jadval,
        'barcha_jadvallar': barcha_jadvallar,
        'tanlangan_ids': tanlangan_ids,
        'statistika': statistika,
        'tanlangan_jadvallar': tanlangan_jadvallar,
    })


@login_required
def sozlamalar(request):
    message = None
    error = None

    if request.method == 'POST':
        eski_parol = request.POST.get('eski_parol')
        yangi_parol1 = request.POST.get('yangi_parol1')
        yangi_parol2 = request.POST.get('yangi_parol2')

        if not request.user.check_password(eski_parol):
            error = "Eski parol noto'g'ri!"
        elif yangi_parol1 != yangi_parol2:
            error = "Yangi parollar mos kelmadi!"
        elif len(yangi_parol1) < 8:
            error = "Parol kamida 8 ta belgidan iborat bo'lishi kerak!"
        elif not re.search(r'[A-Z]', yangi_parol1):
            error = "Parolda kamida 1 ta katta harf bo'lishi kerak (A-Z)!"
        elif not re.search(r'[0-9]', yangi_parol1):
            error = "Parolda kamida 1 ta raqam bo'lishi kerak (0-9)!"
        else:
            request.user.set_password(yangi_parol1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            message = "Parol muvaffaqiyatli yangilandi!"

    return render(request, 'accounts/sozlamalar.html', {
        'message': message,
        'error': error
    })

@login_required
def session_yangilash(request):
    request.session.modified = True
    return JsonResponse({'status': 'ok'})