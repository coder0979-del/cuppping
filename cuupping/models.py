from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# ==========================================
# 1. نموذج المريض (Patient Profile)
# ==========================================
class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'ذكر'),
        ('F', 'أنثى'),
    ]

    full_name = models.CharField(max_length=150, verbose_name="اسم المريض بالكامل")
    phone = models.CharField(max_length=20, unique=True, verbose_name="رقم الهاتف")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="الجنس")
    age = models.PositiveIntegerField(verbose_name="العمر")
    chronic_diseases = models.TextField(blank=True, null=True, verbose_name="الأمراض المزمنة / التنبيهات الطبية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")

    def __str__(self):
        return f"{self.full_name} ({self.phone})"

    class Meta:
        verbose_name = "مريض"
        verbose_name_plural = "السجل الطبي - المرضى"


# ==========================================
# 2. نموذج الموعد والحجز (Appointment)
# ==========================================
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'في الانتظار'),
        ('in_session', 'في العيادة'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغية'),
    ]

    CUPPING_TYPES = [
        ('preventive', 'حجامة وقائية'),
        ('therapeutic', 'حجامة علاجية'),
        ('dry', 'حجامة جافة'),
        ('massage', 'حجامة متزحلقة'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments', verbose_name="المريض")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_staff': True}, verbose_name="الطبيب المعالج")
    appointment_date = models.DateField(verbose_name="تاريخ الموعد")
    appointment_time = models.TimeField(verbose_name="وقت الموعد")
    cupping_type = models.CharField(max_length=20, choices=CUPPING_TYPES, default='preventive', verbose_name="نوع الحجامة")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='waiting', verbose_name="حالة الحجز")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.appointment_date} ({self.get_status_display()})"

    class Meta:
        verbose_name = "موعد"
        verbose_name_plural = "جدول المواعيد والحجوزات"


# ==========================================
# 3. نموذج جلسة الحجامة الطبية (Cupping Session)
# ==========================================
class CuppingSession(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='session', verbose_name="الموعد المرتبط")
    bp_before = models.CharField(max_length=20, verbose_name="ضغط الدم (قبل الجلسة)")
    bp_after = models.CharField(max_length=20, blank=True, null=True, verbose_name="ضغط الدم (بعد الجلسة)")
    blood_sugar = models.CharField(max_length=20, blank=True, null=True, verbose_name="مستوى السكر في الدم")
    
    # مواضع الكؤوس (يمكن حفظها كنص أو استخدام جداول متعددة)
    cupping_points = models.CharField(max_length=255, help_text="مثال: C7, T1-T2, L4-L5", verbose_name="مواضع الحجامة")
    cups_used_count = models.PositiveIntegerField(default=6, validators=[MinValueValidator(1)], verbose_name="عدد الكؤوس المستخدمة")
    oil_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع الزيت المستخدم")
    doctor_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات وتوصيات الطبيب")
    completed_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ إتمام الجلسة")

    def __str__(self):
        return f"جلسة {self.appointment.patient.full_name} - {self.completed_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "جلسة حجامة"
        verbose_name_plural = "سجلات الجلسات الطبية"


# ==========================================
# 4. نموذج المخزون والمستلزمات (Inventory)
# ==========================================
class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('cups', 'كؤوس استخدام واحد'),
        ('blades', 'مستلزمات معقمة (شفرات)'),
        ('oils', 'زيوت ومطهرات'),
        ('general', 'مستلزمات عامة'),
    ]

    item_code = models.CharField(max_length=30, unique=True, verbose_name="كود الصنف")
    name = models.CharField(max_length=100, verbose_name="اسم الصنف / الأدوات")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="الفئة")
    quantity = models.PositiveIntegerField(default=0, verbose_name="الكمية المتاحة")
    min_quantity_warning = models.PositiveIntegerField(default=20, verbose_name="حد التنبيه عند النقص")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="سعر التكلفة للوحدة")

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_quantity_warning

    def __str__(self):
        return f"{self.name} - ({self.quantity} متوفر)"

    class Meta:
        verbose_name = "صنف مخزون"
        verbose_name_plural = "المخزون والمستلزمات"


# ==========================================
# 5. نموذج المالية والفواتير (Invoice)
# ==========================================
class Invoice(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'نقداً (كاش)'),
        ('card', 'شبكة (مدى/فيزا)'),
        ('paypal', 'باي بال / دفع إلكتروني'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'مدفوعة'),
        ('pending', 'قيد الانتظار'),
        ('cancelled', 'ملغية'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الفاتورة")
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, related_name='invoice', verbose_name="الموعد المرتبط")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ الإجمالي (ر.س)")
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='card', verbose_name="طريقة الدفع")
    status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='paid', verbose_name="حالة الدفع")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإصدار")

    def __str__(self):
        return f"فاتورة {self.invoice_number} - {self.total_amount} ر.س"

    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "المالية والفواتير"