from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.db.models import Q, Sum
from django import forms
from django.core.paginator import Paginator
from .models import *

# ==========================================
# أدوات الحماية وتحديد الصلاحيات (Decorators)
# ==========================================

def reception_required(view_func):
    """حماية الدوال الخاصة بموظف الاستقبال وحظر ما سواها"""
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.groups.filter(name='Receptionists').exists() or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def doctor_required(view_func):
    """حماية الدوال الخاصة بالطبيب المعالج وحظر ما سواها"""
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.groups.filter(name='Doctors').exists() or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrap


# ------------------------------------------
# 1. صفحة الهبوط العامة
# ------------------------------------------
def landing_page(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        cupping_type = request.POST.get('cupping_type')
        appointment_date = request.POST.get('appointment_date')

        patient, _ = Patient.objects.get_or_create(
            phone=phone,
            defaults={'full_name': full_name, 'gender': 'M', 'age': 30}
        )

        Appointment.objects.create(
            patient=patient,
            appointment_date=appointment_date,
            appointment_time='10:00:00',
            cupping_type=cupping_type,
            status='waiting'
        )
        messages.success(request, 'تم إرسال طلب الحجز بنجاح! سيتم التواصل معك لتأكيد الموعد.')
        return redirect('landing_page')

    return render(request, 'landing_page.html', {'show_sidebar': False})


# ------------------------------------------
# 2. لوحة تحكم الاستقبال
# ------------------------------------------
@login_required
@reception_required
def reception_dashboard(request):
    today = timezone.now().date()
    appointments = Appointment.objects.filter(appointment_date=today)
    
    context = {
        'show_sidebar': True,
        'total_appointments': appointments.count(),
        'waiting_count': appointments.filter(status='waiting').count(),
        'in_session_count': appointments.filter(status='in_session').count(),
        'appointments': appointments,
    }
    return render(request, 'reception_dashboard.html', context)


# ------------------------------------------
# 3. لوحة تحكم الطبيب المعالج
# ------------------------------------------
@login_required
@doctor_required
def doctor_dashboard(request):
    today = timezone.now().date()
    waiting_patients = Appointment.objects.filter(appointment_date=today, status='waiting')
    completed_sessions = CuppingSession.objects.filter(completed_at__date=today)

    context = {
        'show_sidebar': True,
        'waiting_patients': waiting_patients,
        'completed_count': completed_sessions.count(),
    }
    return render(request, 'doctor_dashboard.html', context)


# ------------------------------------------
# 4. تسجيل مريض وموعد جديد
# ------------------------------------------
@login_required
@reception_required
@login_required
def add_patient_appointment(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        
        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        cupping_type = request.POST.get('cupping_type')

        # جلب المريض بالهاتف أو إنشاؤه، ثم تحديث الاسم والبيانات
        patient, created = Patient.objects.get_or_create(
            phone=phone,
            defaults={'full_name': full_name, 'gender': gender, 'age': age}
        )

        if not created:
            patient.full_name = full_name
            patient.gender = gender
            patient.age = age
            patient.save()

        # إنشاء الموعد وربطه بالطبيب المسجل
        Appointment.objects.create(
            patient=patient,
            doctor_id=doctor_id if doctor_id else None,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            cupping_type=cupping_type,
            status='waiting'
        )
        messages.success(request, f'تم تسجيل الموعد للمريض {full_name} بنجاح!')
        return redirect('reception_dashboard')

    # جلب المستخدمين المسجلين في مجموعة الأطباء فقط
    doctors = User.objects.filter(groups__name='Doctors')

    return render(request, 'patient_appointment_form.html', {
        'doctors': doctors,
        'show_sidebar': True
    })


# ------------------------------------------
# 5. إجراء وتسجيل جلسة حجامة
# ------------------------------------------
@login_required
@doctor_required
def start_cupping_session(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        bp_before = request.POST.get('bp_before')
        bp_after = request.POST.get('bp_after')
        blood_sugar = request.POST.get('blood_sugar')
        cups_count = int(request.POST.get('cups_count', 6))
        points = ", ".join(request.POST.getlist('points'))
        oil_type = request.POST.get('oil_type')
        doctor_notes = request.POST.get('doctor_notes')

        CuppingSession.objects.create(
            appointment=appointment,
            bp_before=bp_before,
            bp_after=bp_after,
            blood_sugar=blood_sugar,
            cupping_points=points,
            cups_used_count=cups_count,
            oil_type=oil_type,
            doctor_notes=doctor_notes
        )

        appointment.status = 'completed'
        appointment.save()

        # خصم الكؤوس تلقائياً من المخزون
        cup_item = InventoryItem.objects.filter(category='cups').first()
        if cup_item and cup_item.quantity >= cups_count:
            cup_item.quantity -= cups_count
            cup_item.save()

        return redirect('doctor_dashboard')

    return render(request, 'cupping_session_form.html', {'appointment': appointment, 'show_sidebar': False})


# ------------------------------------------
# 6. إدارة المخزون
# ------------------------------------------
@login_required
def inventory_list(request):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    items = InventoryItem.objects.all()
    return render(request, 'inventory_list.html', {
        'items': items,
        'show_sidebar': True,
        'is_receptionist': is_receptionist
    })

@login_required
def add_inventory_item(request):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    if request.method == 'POST':
        item_code = request.POST.get('item_code')
        name = request.POST.get('name')
        category = request.POST.get('category')
        quantity = int(request.POST.get('quantity', 0))
        unit_price = float(request.POST.get('unit_price', 0.0))

        InventoryItem.objects.create(
            item_code=item_code,
            name=name,
            category=category,
            quantity=quantity,
            unit_price=unit_price
        )
        messages.success(request, f'تم إضافة الصنف {name} بنجاح!')
        return redirect('inventory_list')

    return render(request, 'add_inventory_item.html', {'show_sidebar': True})

@login_required
def add_inventory_stock(request, item_id):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    item = get_object_or_404(InventoryItem, id=item_id)

    if request.method == 'POST':
        added_quantity = int(request.POST.get('quantity', 0))
        if added_quantity > 0:
            item.quantity += added_quantity
            item.save()
            messages.success(request, f'تم توريد {added_quantity} إلى {item.name} بنجاح.')
        else:
            messages.error(request, 'يرجى إدخال كمية توريد صالحة.')

    return redirect('inventory_list')

@login_required
def edit_inventory_item(request, item_id):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    item = get_object_or_404(InventoryItem, id=item_id)

    if request.method == 'POST':
        item.item_code = request.POST.get('item_code', item.item_code)
        item.name = request.POST.get('name', item.name)
        item.category = request.POST.get('category', item.category)
        item.quantity = int(request.POST.get('quantity', item.quantity))
        item.unit_price = float(request.POST.get('unit_price', item.unit_price))

        item.save()
        messages.success(request, f'تم تعديل بيانات الصنف {item.name} بنجاح!')
        return redirect('inventory_list')

    return render(request, 'edit_inventory_item.html', {
        'item': item,
        'show_sidebar': True
    })

@login_required
def print_invoice(request, invoice_id):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    invoice = get_object_or_404(Invoice, id=invoice_id)

    return render(request, 'print_invoice.html', {
        'invoice': invoice,
        'show_sidebar': False  # إخفاء السايدبار لنسخة الطباعة
    })
# ------------------------------------------
# 7. النظام المالي والفواتير
# ------------------------------------------
@login_required
def finance_list(request):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    search_query = request.GET.get('q', '').strip()
    invoices_list = Invoice.objects.all().order_by('-created_at')

    # البحث السريع باسم المريض أو رقم الهاتف أو رقم الفاتورة
    if search_query:
        invoices_list = invoices_list.filter(
            Q(invoice_number__icontains=search_query) |
            Q(appointment__patient__full_name__icontains=search_query) |
            Q(appointment__patient__phone__icontains=search_query)
        )

    # حساب إجمالي الإيرادات المصفاة
    total_revenue = invoices_list.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0
    pending_amount = invoices_list.filter(status='pending').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0

    # الباجنيشن (10 فواتير في الصفحة)
    paginator = Paginator(invoices_list, 10)
    page_number = request.GET.get('page')
    invoices = paginator.get_page(page_number)

    return render(request, 'finance_list.html', {
        'invoices': invoices,
        'search_query': search_query,
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'show_sidebar': True,
        'is_receptionist': is_receptionist
    })

@login_required
def session_history(request):
    """سجل الجلسات المكتملة مع البحث والتقسيم"""
    search_query = request.GET.get('q', '').strip()
    sessions_list = CuppingSession.objects.all().order_by('-completed_at')

    # البحث السريع باسم المريض، رقم الهاتف، أو التوصيات/الملاحظات
    if search_query:
        sessions_list = sessions_list.filter(
            Q(appointment__patient__full_name__icontains=search_query) |
            Q(appointment__patient__phone__icontains=search_query) |
            Q(doctor_notes__icontains=search_query)
        )

    # الباجنيشن (10 جلسات في الصفحة)
    paginator = Paginator(sessions_list, 10)
    page_number = request.GET.get('page')
    sessions = paginator.get_page(page_number)

    return render(request, 'session_history.html', {
        'sessions': sessions,
        'search_query': search_query,
        'show_sidebar': True
    })

@login_required
def create_invoice(request):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    if request.method == 'POST':
        appointment_id = request.POST.get('appointment')
        total_amount = request.POST.get('total_amount')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status', 'paid')

        appointment = get_object_or_404(Appointment, id=appointment_id)

        if Invoice.objects.filter(appointment=appointment).exists():
            messages.error(request, 'تم إصدار فاتورة لهذا الموعد مسبقاً!')
            return redirect('create_invoice')

        invoice_number = f"INV-{Invoice.objects.count() + 1000}"

        Invoice.objects.create(
            invoice_number=invoice_number,
            appointment=appointment,
            total_amount=total_amount,
            payment_method=payment_method,
            status=status
        )
        messages.success(request, f'تم إصدار الفاتورة رقم {invoice_number} بنجاح!')
        return redirect('finance_list')

    appointments = Appointment.objects.filter(invoice__isnull=True).order_by('-appointment_date')

    return render(request, 'create_invoice.html', {
        'appointments': appointments,
        'show_sidebar': True
    })

@login_required
def mark_invoice_as_paid(request, invoice_id):
    is_receptionist = request.user.groups.filter(name='Receptionists').exists()
    if not (is_receptionist or request.user.is_superuser):
        raise PermissionDenied

    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice.status = 'paid'
    invoice.save()

    messages.success(request, f'تم تحصيل مبلغ الفاتورة {invoice.invoice_number} بنجاح!')
    return redirect('finance_list')


# ------------------------------------------
# 8. إدارة الحسابات
# ------------------------------------------
class EmailRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="البريد الإلكتروني")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

def login_view(request):
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email__iexact=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            messages.success(request, f'مرحباً بك {user.email}')
            return redirect_user_by_role(user)
        else:
            messages.error(request, 'البريد الإلكتروني أو كلمة المرور غير صحيحة.')

    return render(request, 'login.html', {'show_sidebar': False})

def register_view(request):
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == 'POST':
        form = EmailRegisterForm(request.POST)
        role = request.POST.get('role')
        full_name = request.POST.get('full_name', '').strip()  # قراءة الاسم الكامل من الفورم

        email = request.POST.get('email', '').strip()
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'هذا البريد الإلكتروني مُسجل بالفعل.')
        elif form.is_valid():
            user = form.save(commit=False)
            user.username = email  # البريد يظل هو اسم المستخدم للاعتماد عليه في اللوجين
            user.email = email
            
            # حفظ الاسم الكامل في خانات الاسم الخاصة بـ Django
            if full_name:
                name_parts = full_name.split(' ', 1)
                user.first_name = name_parts[0]
                user.last_name = name_parts[1] if len(name_parts) > 1 else ''

            user.save()
            
            if role == 'doctor':
                group, _ = Group.objects.get_or_create(name='Doctors')
                user.groups.add(group)
            elif role == 'receptionist':
                group, _ = Group.objects.get_or_create(name='Receptionists')
                user.groups.add(group)

            login(request, user)
            messages.success(request, 'تم إنشاء الحساب بنجاح!')
            return redirect_user_by_role(user)
    else:
        form = EmailRegisterForm()

    return render(request, 'register.html', {'form': form, 'show_sidebar': False})

def logout_view(request):
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح.')
    return redirect('landing_page')

def redirect_user_by_role(user):
    if user.groups.filter(name='Doctors').exists():
        return redirect('doctor_dashboard')
    elif user.groups.filter(name='Receptionists').exists():
        return redirect('reception_dashboard')
    return redirect('landing_page')