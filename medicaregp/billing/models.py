from django.db import models
from django.utils import timezone
from patients.models import Patient


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Draft',     'Draft'),
        ('Sent',      'Sent'),
        ('Paid',      'Paid'),
        ('Overdue',   'Overdue'),
        ('Cancelled', 'Cancelled'),
    ]

    patient              = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    invoice_number       = models.CharField(max_length=20, unique=True)
    date_issued          = models.DateField()
    due_date             = models.DateField()
    status               = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Draft')
    notes                = models.TextField(blank=True, null=True)
    issued_by            = models.CharField(max_length=100, default='Dr. Tamuka Chivonivoni')

    # ── Medical aid billing ───────────────────────────────────────────────────
    icd10_code           = models.CharField(max_length=20,  blank=True, null=True, verbose_name='ICD-10 code')
    procedure_codes      = models.TextField(blank=True, null=True, verbose_name='Procedure codes', help_text='One per line, e.g. 0190 — Consultation')
    authorization_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Auth. number')
    receipt_number       = models.CharField(max_length=50,  blank=True, null=True)
    amount_paid          = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Amount received (R)')

    class Meta:
        ordering = ['-date_issued']

    def __str__(self):
        return f'{self.invoice_number} — {self.patient}'

    def subtotal(self):
        return sum(item.line_total() for item in self.items.all())

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
    invoice     = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity    = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    procedure_code = models.CharField(max_length=20, blank=True, null=True, verbose_name='Procedure code')

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
