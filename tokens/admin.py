from django.contrib import admin
from .models import Doctor, Slot, Patient, Token, WaitingList


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialization', 'created_at']
    search_fields = ['name', 'specialization']
    list_filter = ['specialization']


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'start_time', 'end_time', 'current_capacity', 'max_capacity', 'status']
    list_filter = ['status', 'doctor', 'start_time']
    search_fields = ['doctor__name']
    date_hierarchy = 'start_time'
    readonly_fields = ['current_capacity']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ['token_number', 'patient', 'slot', 'category', 'priority', 'status', 'estimated_time']
    list_filter = ['status', 'category', 'slot__start_time']
    search_fields = ['patient__name', 'slot__doctor__name']
    readonly_fields = ['priority', 'estimated_time', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    list_display = ['patient', 'slot', 'category', 'priority', 'created_at']
    list_filter = ['category', 'slot__start_time']
    search_fields = ['patient__name']
    readonly_fields = ['priority', 'created_at']
