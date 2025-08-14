from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FiscalProfile

from .models import Client, Invoice


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('email', 'plan', 'is_staff', 'is_active')
    list_filter = ('plan', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password', 'plan')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'plan', 'is_staff', 'is_active')}
        ),
    )

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "tax_id", "is_supplier", "user")
    search_fields = ("name", "tax_id", "email")

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "date", "client", "amount", "vat", "is_confirmed", "user")
    list_filter = ("type", "is_confirmed", "date")
    search_fields = ("description",)

@admin.register(FiscalProfile)
class FiscalProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "business_name", "plan_display")

    def plan_display(self, obj):
        return obj.user.plan
    plan_display.short_description = "Plan"
