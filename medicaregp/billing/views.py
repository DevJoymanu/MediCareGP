from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet, SendEmailForm
import datetime
import re


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
            invoice = form.save()
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
            form.save()
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
