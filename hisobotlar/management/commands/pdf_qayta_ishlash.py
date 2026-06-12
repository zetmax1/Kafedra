"""
Mavjud PDFlardan TalabaYozuv yozuvlarini qayta yaratish.
Eski PDF lar yangi model qo'shilmasdan oldin yuklangan bo'lsa ishlatiladi.

Ishlatish:
    python manage.py pdf_qayta_ishlash
    python manage.py pdf_qayta_ishlash --faqat_bosh   # faqat TalabaYozuv bo'lmagan PDFlar
"""
from django.core.management.base import BaseCommand
from hisobotlar.models import PDFHisobot, ImtihonNatija, TalabaYozuv
from hisobotlar.utils import pdf_dan_malumot_ajrat
import os


class Command(BaseCommand):
    help = "Mavjud PDFlardan TalabaYozuv yozuvlarini qayta yaratish"

    def add_arguments(self, parser):
        parser.add_argument(
            '--faqat_bosh', action='store_true',
            help='Faqat TalabaYozuv bo\'lmagan ImtihonNatijalar uchun ishlat'
        )

    def handle(self, *args, **options):
        natijalar = ImtihonNatija.objects.all().select_related('hisobot')

        if options['faqat_bosh']:
            # TalabaYozuv yo'q bo'lganlarni topish
            natijalar = [n for n in natijalar
                         if not TalabaYozuv.objects.filter(natija=n).exists()]
            self.stdout.write(f"TalabaYozuv bo'lmagan: {len(natijalar)} ta natija")
        else:
            self.stdout.write(f"Jami natijalar: {natijalar.count()} ta")

        muvaffaqiyat = 0
        xato = 0

        for natija in natijalar:
            hisobot = natija.hisobot
            pdf_path = hisobot.fayl.path if hisobot.fayl else None

            if not pdf_path or not os.path.exists(pdf_path):
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ PDF topilmadi: {natija.fan_nomi} | {natija.guruh}"
                ))
                xato += 1
                continue

            # Eski TalabaYozuvlarni o'chirish
            eski = TalabaYozuv.objects.filter(natija=natija).count()
            if eski > 0:
                TalabaYozuv.objects.filter(natija=natija).delete()
                self.stdout.write(f"  🗑 {eski} ta eski yozuv o'chirildi: {natija.fan_nomi}")

            # PDF dan qayta ajratish
            malumot = pdf_dan_malumot_ajrat(pdf_path)

            if malumot['xato']:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Xato: {natija.fan_nomi} | {natija.guruh} — {malumot['xato']}"
                ))
                xato += 1
                continue

            # TalabaYozuv yaratish
            yozuvlar = []
            for t in malumot.get('talabalar', []):
                yozuvlar.append(TalabaYozuv(
                    natija=natija,
                    guruh=natija.guruh,
                    fan_nomi=natija.fan_nomi,
                    fan_oqituvchi=natija.fan_oqituvchi,
                    fio=t['fio'],
                    reyting_raqam=t['reyting_raqam'],
                    joriy=t['joriy'],
                    oraliq=t['oraliq'],
                    joriy_oraliq=t['joriy_oraliq'],
                    yakuniy=t['yakuniy'],
                    ozlashtirish=t['ozlashtirish'],
                    baho=t['baho'],
                ))

            if yozuvlar:
                TalabaYozuv.objects.bulk_create(yozuvlar)
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ {len(yozuvlar)} ta talaba: {natija.fan_nomi} | {natija.guruh}"
                ))
                muvaffaqiyat += 1
            else:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ Talabalar topilmadi: {natija.fan_nomi} | {natija.guruh}"
                ))
                xato += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nNatija: {muvaffaqiyat} ta muvaffaqiyatli, {xato} ta xato"
        ))
