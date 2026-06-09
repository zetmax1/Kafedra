from django.db import models
from django.contrib.auth.models import User
from hisobotlar.models import ExcelJadval

class ExcelQator(models.Model):
    jadval = models.ForeignKey(ExcelJadval, on_delete=models.CASCADE)
    qator_data = models.JSONField()
    # Har bir qator JSON sifatida saqlanadi

    def __str__(self):
        return f"Qator - {self.jadval.fayl.name}"