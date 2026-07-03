from django.db import models
from django.utils import timezone
from patients.models import Patient


class TariffCode(models.Model):
    """A billable tariff (procedure) code, split into Medical vs Surgical
    categories. Rates live on TariffRate so they can change over time
    without touching historical bills."""
    CATEGORY_CHOICES = [
        ('Medical',  'Medical'),
        ('Surgical', 'Surgical'),
    ]
    code        = models.CharField(max_length=20, unique=True, verbose_name='Tariff code')
    description = models.CharField(max_length=255)
    category    = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='Medical')
    active      = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'code']

    def __str__(self):
        return f'{self.code} — {self.description} ({self.category})'

    def rate_on(self, date):
        """The rate in force on `date` — the latest TariffRate whose
        effective_from is on or before that date. Returns None if the code
        had no rate yet."""
        return self.rates.filter(effective_from__lte=date).order_by('-effective_from').first()

    def current_rate(self):
        return self.rate_on(timezone.now().date())


class TariffRate(models.Model):
    """One priced period of a tariff. Rate changes APPEND a new row with a
    later effective_from — existing rows are never edited, so a bill issued
    under an old rate can always be reproduced. Invoice items additionally
    snapshot unit_price at billing time, so issued bills never change even
    if a rate row were corrected."""
    tariff         = models.ForeignKey(TariffCode, on_delete=models.CASCADE, related_name='rates')
    effective_from = models.DateField()
    amount         = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Rate (R)')

    class Meta:
        unique_together = [('tariff', 'effective_from')]
        ordering = ['tariff__code', '-effective_from']

    def __str__(self):
        return f'{self.tariff.code} @ R{self.amount} from {self.effective_from}'


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Draft',     'Draft'),
        ('Sent',      'Sent'),
        ('Paid',      'Paid'),
        ('Overdue',   'Overdue'),
        ('Cancelled', 'Cancelled'),
    ]

    patient              = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    consultation         = models.ForeignKey(
        'consultations.Consultation',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices', verbose_name='Linked consultation',
    )
    invoice_number       = models.CharField(max_length=20, unique=True)
    date_issued          = models.DateField()
    due_date             = models.DateField()
    status               = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Draft')
    notes                = models.TextField(blank=True, null=True)
    issued_by            = models.CharField(max_length=100, default='Dr. Tamuka Chivonivoni')

    # ── Medical aid billing ───────────────────────────────────────────────────
    icd10_code           = models.TextField(blank=True, null=True, verbose_name='ICD-10 code(s)')
    procedure_codes      = models.TextField(blank=True, null=True, verbose_name='Procedure codes', help_text='One per line, e.g. 0190 — Consultation')
    authorization_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Auth. number')
    receipt_number       = models.CharField(max_length=50,  blank=True, null=True)
    amount_paid          = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Amount received (R)')

    class Meta:
        ordering = ['-date_issued']

    def __str__(self):
        return f'{self.invoice_number} — {self.patient}'

    @property
    def icd10_codes_list(self):
        import json
        if not self.icd10_code:
            return []
        try:
            parsed = json.loads(self.icd10_code)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return [{'code': self.icd10_code, 'description': self.icd10_code}]

    def subtotal(self):
        return sum(item.line_total() for item in self.items.all())

    # ── Medical vs surgical split ─────────────────────────────────────────────
    def medical_items(self):
        return [i for i in self.items.all() if i.category == 'Medical']

    def surgical_items(self):
        return [i for i in self.items.all() if i.category == 'Surgical']

    def medical_subtotal(self):
        return round(sum(i.line_total() for i in self.medical_items()), 2)

    def surgical_subtotal(self):
        return round(sum(i.line_total() for i in self.surgical_items()), 2)

    def vat_amount(self, rate=15):
        return round(self.subtotal() * rate / 100, 2)

    def total(self, vat_rate=15):
        return round(self.subtotal() + self.vat_amount(vat_rate), 2)

    def amount_received(self):
        payments_total = sum(float(p.amount) for p in self.payments.all())
        return payments_total if payments_total else float(self.amount_paid or 0)

    def balance_due(self):
        return round(self.total() - self.amount_received(), 2)


class InvoiceItem(models.Model):
    LINE_TYPE_CHOICES = [
        ('Procedure',  'Procedure'),
        ('Modifier',   'Modifier'),
        ('Medicine',   'Medicine'),
        ('Consumable', 'Consumable'),
    ]

    CATEGORY_CHOICES = TariffCode.CATEGORY_CHOICES

    invoice        = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    line_type      = models.CharField(max_length=20, choices=LINE_TYPE_CHOICES, default='Procedure', verbose_name='Line type')
    # Link to the versioned tariff catalogue. unit_price stays a SNAPSHOT of
    # the rate at billing time — later tariff changes never alter this line.
    tariff         = models.ForeignKey(TariffCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items')
    category       = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='Medical', verbose_name='Medical / Surgical')
    procedure_code = models.CharField(max_length=20, blank=True, null=True, verbose_name='Tariff code')
    nappi_code     = models.CharField(max_length=20, blank=True, null=True, verbose_name='NAPPI code')
    description    = models.CharField(max_length=255, blank=True, null=True, verbose_name='NAPPI description')
    diag_code      = models.CharField(max_length=20, blank=True, null=True, verbose_name='Diagnosis code')
    quantity       = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    unit_price     = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Category always follows the linked tariff's category; free-typed
        # lines keep whatever was chosen manually.
        if self.tariff_id:
            self.category = self.tariff.category
        super().save(*args, **kwargs)

    def line_total(self):
        return round(float(self.quantity) * float(self.unit_price), 2)

    def __str__(self):
        return f'{self.description} x{self.quantity}'


class Payment(models.Model):
    METHOD_CHOICES = [
        ('Cash',        'Cash'),
        ('Card',        'Card'),
        ('EFT',         'EFT / Bank Transfer'),
        ('Medical Aid', 'Medical Aid'),
    ]
    invoice        = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    date           = models.DateField()
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    method         = models.CharField(max_length=20, choices=METHOD_CHOICES)
    reference      = models.CharField(max_length=100, blank=True, null=True, verbose_name='Reference / EFT ref')
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)
    notes          = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'REC-{self.receipt_number}  R{self.amount}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.receipt_number:
            self.receipt_number = f'{self.pk:06d}'
            Payment.objects.filter(pk=self.pk).update(receipt_number=self.receipt_number)


class ClaimSubmission(models.Model):
    STATUS_CHOICES = [
        ('Submitted',   'Submitted'),
        ('Accepted',    'Accepted'),
        ('Rejected',    'Rejected'),
        ('Resubmitted', 'Resubmitted'),
        ('Paid',        'Paid'),
    ]
    invoice              = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='claim_submissions')
    submitted_at         = models.DateTimeField(auto_now_add=True)
    scheme_name          = models.CharField(max_length=100)
    submission_reference = models.CharField(max_length=100, blank=True, null=True, verbose_name='Submission / batch reference')
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Submitted')
    rejection_code       = models.CharField(max_length=50, blank=True, null=True, verbose_name='Rejection code')
    rejection_reason     = models.TextField(blank=True, null=True)
    resubmission_notes   = models.TextField(blank=True, null=True)
    parent               = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='resubmissions', verbose_name='Resubmission of')
    resolved_at          = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.invoice.invoice_number} — {self.scheme_name} — {self.status}'
