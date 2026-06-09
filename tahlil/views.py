from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import ExcelJadval, ExcelQator
import pandas as pd
import json
import os
import re


@login_required
def tahlil_list(request):
    jadvallar = ExcelJadval.objects.filter(
        yuklagan_user=request.user
    ).order_by('-yuklangan_vaqt')
    return render(request, 'tahlil/list.html', {'jadvallar': jadvallar})


@login_required
def excel_yuklash(request):
    if request.method == 'POST':
        yuklash_turi = request.POST.get('yuklash_turi')  # 'excel' yoki 'sheets'

        try:
            if yuklash_turi == 'excel':
                fayl = request.FILES.get('excel_fayl')
                if not fayl:
                    messages.error(request, "Fayl tanlanmadi!")
                    return redirect('excel_yuklash')

                if not fayl.name.endswith(('.xlsx', '.xls')):
                    messages.error(request, "Faqat .xlsx yoki .xls fayl yuklansin!")
                    return redirect('excel_yuklash')

                # Faylni o'qish
                df = pd.read_excel(fayl)

            elif yuklash_turi == 'sheets':
                sheets_url = request.POST.get('sheets_url', '').strip()
                if not sheets_url:
                    messages.error(request, "Google Sheets havolasi kiritilmadi!")
                    return redirect('excel_yuklash')

                # Google Sheets URL dan ID ajratish
                # https://docs.google.com/spreadsheets/d/ID/edit
                match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheets_url)
                if not match:
                    messages.error(request, "Google Sheets havolasi noto'g'ri!")
                    return redirect('excel_yuklash')

                sheet_id = match.group(1)
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

                df = pd.read_csv(csv_url)
                fayl = None

            else:
                messages.error(request, "Yuklash turi tanlanmadi!")
                return redirect('excel_yuklash')

            # Bo'sh ustunlarni olib tashlash
            df = df.dropna(how='all', axis=1)
            df = df.dropna(how='all', axis=0)

            # Ustun nomlarini olish
            ustunlar = list(df.columns.astype(str))

            # Bazaga saqlash
            jadval = ExcelJadval.objects.create(
                fayl=fayl if fayl else '',
                yuklagan_user=request.user,
                ustunlar=ustunlar
            )

            # Qatorlarni saqlash
            for _, row in df.iterrows():
                qator_data = {}
                for ustun in ustunlar:
                    qiymat = row.get(ustun)
                    # NaN qiymatlarni bo'sh string ga aylantirish
                    if pd.isna(qiymat) if not isinstance(qiymat, str) else False:
                        qiymat = ''
                    else:
                        qiymat = str(qiymat) if not isinstance(qiymat, str) else qiymat
                    qator_data[ustun] = qiymat

                ExcelQator.objects.create(
                    jadval=jadval,
                    qator_data=qator_data
                )

            messages.success(
                request,
                f"Jadval muvaffaqiyatli yuklandi! "
                f"{len(ustunlar)} ta ustun, {df.shape[0]} ta qator."
            )
            return redirect('jadval_korish', pk=jadval.pk)

        except Exception as e:
            messages.error(request, f"Xato: {str(e)}")
            return redirect('excel_yuklash')

    return render(request, 'tahlil/yuklash.html')


@login_required
def jadval_korish(request, pk):
    import json
    jadval = get_object_or_404(ExcelJadval, pk=pk, yuklagan_user=request.user)
    barcha_qatorlar = list(ExcelQator.objects.filter(jadval=jadval))

    ustunlar = jadval.ustunlar

    # Qatorlarni list of list formatida saqlash (index asosida)
    qatorlar_list = []
    for q in barcha_qatorlar:
        qator = [str(q.qator_data.get(ustun, '') or '') for ustun in ustunlar]
        qatorlar_list.append(qator)

    # Har ustun uchun unikal qiymatlar (index asosida)
    unikal = {}
    for idx, ustun in enumerate(ustunlar):
        qiymatlar = list(set(
            str(q.qator_data.get(ustun, '') or '')
            for q in barcha_qatorlar
            if q.qator_data.get(ustun, '')
        ))
        qiymatlar.sort()
        unikal[idx] = qiymatlar

    return render(request, 'tahlil/korish.html', {
        'jadval': jadval,
        'qatorlar': barcha_qatorlar,
        'ustunlar_json': json.dumps(ustunlar, ensure_ascii=False),
        'unikal_json': json.dumps(unikal, ensure_ascii=False),
        'qatorlar_json': json.dumps(qatorlar_list, ensure_ascii=False),
        'filtr_ustun': '',
        'filtr_qiymat': '',
        'tartib_ustun': '',
    })

@login_required
def jadval_ochirish(request, pk):
    jadval = get_object_or_404(ExcelJadval, pk=pk, yuklagan_user=request.user)
    if request.method == 'POST':
        if jadval.fayl and hasattr(jadval.fayl, 'path'):
            try:
                if os.path.isfile(jadval.fayl.path):
                    os.remove(jadval.fayl.path)
            except Exception:
                pass
        jadval.delete()
        messages.success(request, "Jadval muvaffaqiyatli o'chirildi!")
    return redirect('tahlil')