from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email manzil")

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu email allaqachon mavjud!")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # Username sifatida email ishlatamiz
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_active')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu email allaqachon mavjud!")
        return email


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Qo'shimcha ma'lumot"


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    inlines = [UserProfileInline]

    # Yangi user qo'shishda ko'rinadigan maydonlar
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    # Mavjud userni tahrirlashda ko'rinadigan maydonlar
    fieldsets = (
        ("Asosiy ma'lumotlar", {'fields': ('email', 'username')}),
        ("Shaxsiy ma'lumotlar", {'fields': ('first_name', 'last_name')}),
        ("Ruxsatlar", {'fields': ('is_active',)}),
    )

    list_display = ('email', 'first_name', 'last_name', 'is_active', 'date_joined')
    list_filter = ('is_active',)
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Admin o'zini o'chira olmasin
    def has_delete_permission(self, request, obj=None):
        if obj and obj == request.user:
            return False
        return True


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)