from django.contrib import admin
from .models import *


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'gender', 'age', 'created_at')
    search_fields = ('full_name', 'phone')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'cupping_type', 'status')
    list_filter = ('status', 'appointment_date', 'cupping_type')


@admin.register(CuppingSession)
class CuppingSessionAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'cups_used_count', 'bp_before', 'completed_at')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_code', 'name', 'category', 'quantity', 'min_quantity_warning', 'is_low_stock')
    list_filter = ('category',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'appointment', 'total_amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method')