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

class ExcelJadval(models.Model):
    fayl = models.FileField(upload_to='excel_fayllar/')
    yuklangan_vaqt = models.DateTimeField(auto_now_add=True)
    yuklagan_user = models.ForeignKey(User, on_delete=models.CASCADE)
    ustunlar = models.JSONField(default=list)
    # Avtomatik aniqlangan ustun nomlari saqlanadi

    def __str__(self):
        return f"{self.fayl.name} - {self.yuklangan_vaqt}"