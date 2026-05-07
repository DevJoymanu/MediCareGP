from django.db import models
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

    def balance_due(self):
        paid = float(self.amount_paid or 0)
        return round(self.total() - paid, 2)


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
