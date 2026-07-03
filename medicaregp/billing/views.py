import csv
import datetime
import io
import json
import os
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone

# ── NAPPI code data (loaded once, cached in module) ───────────────────────────
_NAPPI_DATA = None

def _get_nappi_data():
    global _NAPPI_DATA
    if _NAPPI_DATA is None:
        path = os.path.join(os.path.dirname(__file__), 'nappi_data.json')
        with open(path, 'r', encoding='utf-8') as f:
            _NAPPI_DATA = json.load(f)
    return _NAPPI_DATA

from .models import Invoice, InvoiceItem, Payment, ClaimSubmission, TariffCode
from .forms import (InvoiceForm, InvoiceItemFormSet, SendEmailForm,
                    PaymentForm, ClaimSubmissionForm, ClaimUpdateForm, ERAImportForm)
from . import bhf as bhf_generator


def _next_invoice_number():
    today = timezone.now().date()
    prefix = f'INV-{today.strftime("%Y%m")}-'
    last = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
    if last:
        try:
            seq = int(last.invoice_number.split('-')[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f'{prefix}{seq:03d}'


@login_required
def invoice_list(request):
    status_filter = request.GET.get('status', '')
    invoices = Invoice.objects.select_related('patient').prefetch_related('items')
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    # Flag overdue unpaid invoices
    today = timezone.now().date()
    for inv in invoices:
        if inv.status in ('Sent', 'Draft') and inv.due_date < today:
            if inv.status != 'Overdue':
                inv.status = 'Overdue'
                inv.save(update_fields=['status'])

    totals = {
        'draft':     Invoice.objects.filter(status='Draft').count(),
        'sent':      Invoice.objects.filter(status='Sent').count(),
        'paid':      Invoice.objects.filter(status='Paid').count(),
        'overdue':   Invoice.objects.filter(status='Overdue').count(),
    }

    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices,
        'status_filter': status_filter,
        'totals': totals,
    })


@login_required
def patient_consultations(request, patient_id):
    from consultations.models import Consultation
    qs = Consultation.objects.filter(patient_id=patient_id).order_by('-date', '-pk')[:50]
    data = []
    for c in qs:
        snippet = c.chief_complaint or c.assessment or ''
        if snippet:
            snippet = snippet[:60] + ('…' if len(snippet) > 60 else '')
        else:
            snippet = '(no notes)'
        data.append({'id': c.pk, 'label': f'{c.date} — {snippet}'})
    return JsonResponse({'consultations': data})


@login_required
def consultation_icd10(request, consultation_id):
    from consultations.models import Consultation
    c = get_object_or_404(Consultation, pk=consultation_id)
    return JsonResponse({
        'icd10_codes': c.icd10_codes_list,
        'assessment': c.assessment or '',
    })


@login_required
def search_nappi(request):
    q = request.GET.get('q', '').strip().lower()
    if len(q) < 2:
        return JsonResponse({'results': []})
    data = _get_nappi_data()
    results = [
        item for item in data
        if item['code'].startswith(q) or q in item['desc'].lower()
    ][:12]
    return JsonResponse({'results': results})


@login_required
def invoice_create(request):
    today = timezone.now().date()
    patient_id = request.GET.get('patient_id', '')
    initial = {
        'invoice_number': _next_invoice_number(),
        'date_issued': today,
        'due_date': today + datetime.timedelta(days=30),
    }
    if patient_id:
        initial['patient'] = patient_id

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            consultation_id = request.POST.get('consultation_id', '').strip()
            if consultation_id:
                try:
                    invoice.consultation_id = int(consultation_id)
                except (ValueError, TypeError):
                    pass
            invoice.save()
            formset.instance = invoice
            formset.save()
            messages.success(request, f'Invoice {invoice.invoice_number} created.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(initial=initial)
        formset = InvoiceItemFormSet()

    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Invoice',
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'billing/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            updated = form.save(commit=False)
            consultation_id = request.POST.get('consultation_id', '').strip()
            if consultation_id:
                try:
                    updated.consultation_id = int(consultation_id)
                except (ValueError, TypeError):
                    updated.consultation_id = None
            else:
                updated.consultation_id = None
            updated.save()
            formset.save()
            messages.success(request, 'Invoice updated.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice)

    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit {invoice.invoice_number}',
        'invoice': invoice,
    })


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        num = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'Invoice {num} deleted.')
        return redirect('invoice_list')
    return render(request, 'billing/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'billing/invoice_print.html', {'invoice': invoice})


@login_required
def invoice_send_email(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    patient = invoice.patient

    default_to    = patient.email or ''
    default_subj  = f'Invoice {invoice.invoice_number} from Dr. Tamuka Chivonivoni'
    default_msg   = (
        f'Dear {patient.first_name},\n\n'
        f'Please find attached your invoice {invoice.invoice_number} '
        f'dated {invoice.date_issued.strftime("%d %B %Y")} '
        f'for R{invoice.total():,.2f}, due by {invoice.due_date.strftime("%d %B %Y")}.\n\n'
        f'Please contact us if you have any queries.\n\n'
        f'Kind regards,\nDr. Tamuka Chivonivoni\nGeneral Practitioner'
    )

    if request.method == 'POST':
        form = SendEmailForm(request.POST)
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            subject  = form.cleaned_data['subject']
            body     = form.cleaned_data['message']

            html_body = render_to_string('billing/email_invoice.html', {
                'invoice': invoice,
                'message': body,
            })

            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=body,
                    from_email='noreply@gp-crm.co.za',
                    to=[to_email],
                )
                email.attach_alternative(html_body, 'text/html')
                email.send()

                if invoice.status == 'Draft':
                    invoice.status = 'Sent'
                    invoice.save(update_fields=['status'])

                messages.success(request, f'Invoice emailed to {to_email}.')
                return redirect('invoice_detail', pk=invoice.pk)
            except Exception as e:
                messages.error(request, f'Failed to send email: {e}')
    else:
        form = SendEmailForm(initial={
            'to_email': default_to,
            'subject':  default_subj,
            'message':  default_msg,
        })

    return render(request, 'billing/invoice_send_email.html', {
        'invoice': invoice,
        'form': form,
    })


@login_required
def invoice_mark_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.status = 'Paid'
        invoice.save(update_fields=['status'])
        messages.success(request, f'Invoice {invoice.invoice_number} marked as paid.')
    return redirect('invoice_detail', pk=invoice.pk)


# ── Payments / receipts ───────────────────────────────────────────────────────

@login_required
def payment_add(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            if invoice.balance_due() <= 0 and invoice.status != 'Paid':
                invoice.status = 'Paid'
                invoice.save(update_fields=['status'])
            messages.success(request, f'Payment of R{payment.amount} recorded. Receipt {payment.receipt_number}.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = PaymentForm(initial={'date': timezone.now().date(), 'method': 'Cash'})
    return render(request, 'billing/payment_form.html', {'form': form, 'invoice': invoice})


@login_required
def receipt_print(request, payment_pk):
    payment = get_object_or_404(Payment, pk=payment_pk)
    return render(request, 'billing/receipt_print.html', {'payment': payment})


# ── Claim submissions ─────────────────────────────────────────────────────────

@login_required
def claim_submit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = ClaimSubmissionForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.invoice = invoice
            claim.save()
            messages.success(request, f'Claim logged as submitted to {claim.scheme_name}.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        scheme = invoice.patient.medical_aid_name or ''
        form = ClaimSubmissionForm(initial={'scheme_name': scheme})
    return render(request, 'billing/claim_form.html', {'form': form, 'invoice': invoice})


@login_required
def claim_update(request, claim_pk):
    claim = get_object_or_404(ClaimSubmission, pk=claim_pk)
    if request.method == 'POST':
        form = ClaimUpdateForm(request.POST, instance=claim)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.status in ('Accepted', 'Paid', 'Rejected') and not updated.resolved_at:
                updated.resolved_at = timezone.now()
            if updated.status == 'Resubmitted':
                ClaimSubmission.objects.create(
                    invoice=claim.invoice,
                    scheme_name=claim.scheme_name,
                    status='Submitted',
                    resubmission_notes=updated.resubmission_notes,
                    parent=claim,
                )
                updated.status = 'Resubmitted'
            updated.save()
            messages.success(request, 'Claim status updated.')
            return redirect('invoice_detail', pk=claim.invoice.pk)
    else:
        form = ClaimUpdateForm(instance=claim)
    return render(request, 'billing/claim_update.html', {'form': form, 'claim': claim})


# ── ERA import ────────────────────────────────────────────────────────────────

@login_required
def era_import(request):
    results = []
    if request.method == 'POST':
        form = ERAImportForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['csv_file']
            decoded = f.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))
            for row in reader:
                inv_num   = (row.get('invoice_number') or '').strip()
                amount    = (row.get('amount_paid')    or '').strip()
                date_paid = (row.get('date_paid')      or '').strip()
                reference = (row.get('reference')      or '').strip()
                notes_val = (row.get('notes')          or '').strip()

                if not inv_num or not amount or not date_paid:
                    results.append({'row': inv_num or '?', 'status': 'error', 'msg': 'Missing required fields'})
                    continue
                try:
                    invoice = Invoice.objects.get(invoice_number=inv_num)
                except Invoice.DoesNotExist:
                    results.append({'row': inv_num, 'status': 'error', 'msg': 'Invoice not found'})
                    continue
                try:
                    paid_date = datetime.date.fromisoformat(date_paid)
                except ValueError:
                    results.append({'row': inv_num, 'status': 'error', 'msg': f'Bad date format: {date_paid}'})
                    continue
                payment = Payment.objects.create(
                    invoice=invoice,
                    date=paid_date,
                    amount=float(amount),
                    method='Medical Aid',
                    reference=reference or None,
                    notes=notes_val or None,
                )
                if invoice.balance_due() <= 0 and invoice.status != 'Paid':
                    invoice.status = 'Paid'
                    invoice.save(update_fields=['status'])
                results.append({'row': inv_num, 'status': 'ok', 'msg': f'Payment R{amount} recorded (REC-{payment.receipt_number})'})
    else:
        form = ERAImportForm()
    return render(request, 'billing/era_import.html', {'form': form, 'results': results})


# ── EDI export ────────────────────────────────────────────────────────────────

@login_required
def bhf_export(request, pk):
    """Generate and download a BHF-format claim file for Healthbridge portal upload."""
    invoice  = get_object_or_404(Invoice, pk=pk)
    content  = bhf_generator.generate(invoice)
    filename = f'claim_{invoice.invoice_number}.bhf'
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def edi_export(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    patient = invoice.patient

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="claim_{invoice.invoice_number}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Invoice Number',      invoice.invoice_number])
    writer.writerow(['Date Issued',         invoice.date_issued])
    writer.writerow(['Doctor',              invoice.issued_by])
    writer.writerow(['ICD-10 Code',         invoice.icd10_code or ''])
    writer.writerow(['Authorization Number', invoice.authorization_number or ''])
    writer.writerow(['Patient Surname',     patient.last_name])
    writer.writerow(['Patient First Name',  patient.first_name])
    writer.writerow(['Patient ID Number',   patient.id_number])
    writer.writerow(['Patient DOB',         patient.date_of_birth])
    writer.writerow(['Medical Aid Scheme',  patient.medical_aid_name or ''])
    writer.writerow(['Medical Aid Plan',    patient.medical_aid_plan or ''])
    writer.writerow(['Membership Number',   patient.medical_aid_number or ''])
    writer.writerow(['Principal Member',    patient.principal_member_name or ''])
    writer.writerow(['Principal Member ID', patient.principal_member_id or ''])
    writer.writerow(['Dependant Code',      patient.dependant_code or ''])
    writer.writerow([])
    writer.writerow(['Procedure Code', 'Description', 'Qty', 'Unit Price (R)', 'Line Total (R)'])
    for item in invoice.items.all():
        writer.writerow([item.procedure_code or '', item.description,
                         item.quantity, item.unit_price, item.line_total()])
    writer.writerow([])
    writer.writerow(['Subtotal', invoice.subtotal()])
    writer.writerow(['VAT (15%)', invoice.vat_amount()])
    writer.writerow(['Total', invoice.total()])
    return response


# ── Versioned tariff catalogue ─────────────────────────────────────────────────

@login_required
def tariff_list(request):
    """Tariff catalogue, split Medical vs Surgical, with the rate currently in
    force. Rates are versioned in admin: a price change appends a new
    TariffRate row — issued invoices keep their snapshotted unit_price."""
    today = timezone.now().date()
    tariffs = TariffCode.objects.filter(active=True).prefetch_related('rates')
    rows = [{'tariff': t, 'rate': t.rate_on(today), 'history': t.rates.all()} for t in tariffs]
    return render(request, 'billing/tariff_list.html', {
        'medical':  [r for r in rows if r['tariff'].category == 'Medical'],
        'surgical': [r for r in rows if r['tariff'].category == 'Surgical'],
        'today': today,
    })


@login_required
def tariff_rate_lookup(request):
    """JSON: rate for a tariff code on a given date (defaults to today) —
    used by the invoice form to prefill unit_price from the catalogue."""
    code = request.GET.get('code', '').strip()
    date_str = request.GET.get('date', '')
    try:
        on_date = datetime.date.fromisoformat(date_str) if date_str else timezone.now().date()
    except ValueError:
        on_date = timezone.now().date()
    tariff = TariffCode.objects.filter(code=code, active=True).first()
    if not tariff:
        return JsonResponse({'found': False})
    rate = tariff.rate_on(on_date)
    return JsonResponse({
        'found': True,
        'code': tariff.code,
        'description': tariff.description,
        'category': tariff.category,
        'rate': str(rate.amount) if rate else None,
        'effective_from': rate.effective_from.isoformat() if rate else None,
    })
