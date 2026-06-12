from django.db import models
from django.contrib.auth.models import User


class PDFHisobot(models.Model):
    fayl = models.FileField(upload_to='pdf_fayllar/')
    yuklangan_vaqt = models.DateTimeField(auto_now_add=True)
    yuklagan_user = models.ForeignKey(User, on_delete=models.CASCADE)
    holat = models.CharField(max_length=20, default='kutilmoqda')
    # holat: kutilmoqda / muvaffaqiyatli / xato

    def __str__(self):
        return f"{self.fayl.name} - {self.yuklangan_vaqt}"


class ImtihonNatija(models.Model):
    hisobot = models.ForeignKey(PDFHisobot, on_delete=models.CASCADE)
    fan_nomi = models.CharField(max_length=200)
    fan_oqituvchi = models.CharField(max_length=200)
    guruh = models.CharField(max_length=100)
    jami_talabalar = models.IntegerField(default=0)
    baho_5 = models.IntegerField(default=0)
    baho_4 = models.IntegerField(default=0)
    baho_3 = models.IntegerField(default=0)
    kelmadi = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.fan_nomi} - {self.guruh}"


class TalabaYozuv(models.Model):
    """
    Har bir PDF dagi har bir talabaning batafsil ma'lumoti.
    ImtihonNatija ga bog'liq (cascade o'chadi).
    """
    natija = models.ForeignKey(
        ImtihonNatija,
        on_delete=models.CASCADE,
        related_name='talabalar'
    )

    # Guruh, fan, o'qituvchi — tezkor filtrlash uchun ImtihonNatija dan nusxalanadi
    guruh = models.CharField(max_length=100, db_index=True)
    fan_nomi = models.CharField(max_length=200, db_index=True)
    fan_oqituvchi = models.CharField(max_length=200, db_index=True)

    # Talaba ma'lumotlari
    fio = models.CharField(max_length=300)
    reyting_raqam = models.CharField(max_length=20, blank=True)

    # Ballar
    joriy = models.IntegerField(default=0)        # ΣJN
    oraliq = models.IntegerField(default=0)       # ΣON
    joriy_oraliq = models.IntegerField(default=0) # ΣJN + ΣON
    yakuniy = models.IntegerField(default=0)      # YN
    ozlashtirish = models.IntegerField(default=0) # O'zlashtirish ko'rsatkichi
    baho = models.IntegerField(default=0)         # 3 / 4 / 5

    class Meta:
        ordering = ['guruh', 'fio']
        indexes = [
            models.Index(fields=['guruh', 'fan_nomi']),
            models.Index(fields=['fan_oqituvchi']),
        ]

    def __str__(self):
        return f"{self.fio} | {self.guruh} | {self.fan_nomi}"


class ExcelJadval(models.Model):
    fayl = models.FileField(upload_to='excel_fayllar/')
    yuklangan_vaqt = models.DateTimeField(auto_now_add=True)
    yuklagan_user = models.ForeignKey(User, on_delete=models.CASCADE)
    ustunlar = models.JSONField(default=list)
    # Avtomatik aniqlangan ustun nomlari saqlanadi

    def __str__(self):
        return f"{self.fayl.name} - {self.yuklangan_vaqt}"