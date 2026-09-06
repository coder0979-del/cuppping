from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),

    # مسارات الحسابات
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), 
         name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), 
         name='password_reset_confirm'),

    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
         name='password_reset_complete'),

    # الشاشات
    path('reception/', views.reception_dashboard, name='reception_dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patient/add/', views.add_patient_appointment, name='add_patient_appointment'),
    path('session/start/<int:appointment_id>/', views.start_cupping_session, name='start_cupping_session'),
    
    # المالية
    path('finance/print/<int:invoice_id>/', views.print_invoice, name='print_invoice'),
    path('finance/', views.finance_list, name='finance_list'),
    path('finance/pay/<int:invoice_id>/', views.mark_invoice_as_paid, name='mark_invoice_as_paid'),
    path('finance/create/', views.create_invoice, name='create_invoice'),
    
    # المخزون
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.add_inventory_item, name='add_inventory_item'),
    path('inventory/add-stock/<int:item_id>/', views.add_inventory_stock, name='add_inventory_stock'),
    path('inventory/edit/<int:item_id>/', views.edit_inventory_item, name='edit_inventory_item'),
]