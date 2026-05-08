from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Document
from .forms import DocumentForm

@login_required
def document_list(request):
    from django.db.models import Q, Count
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')

    qs = Document.objects.select_related('patient').all()
    if q:
        qs = qs.filter(
            Q(patient__first_name__icontains=q) | Q(patient__last_name__icontains=q) | Q(doc_type__icontains=q) | Q(category__icontains=q)
        )
    if cat:
        qs = qs.filter(category=cat)

    raw_counts = Document.objects.values('category').annotate(n=Count('id'))
    counts = {c['category']: c['n'] for c in raw_counts}

    categories_with_counts = [
        {'value': v, 'label': label, 'count': counts.get(v, 0)}
        for v, label in Document.CATEGORY_CHOICES
    ]

    grouped = None
    if not cat:
        cat_map = {v: label for v, label in Document.CATEGORY_CHOICES}
        group_map = {}
        for doc in qs:
            key = doc.category
            if key not in group_map:
                group_map[key] = {'value': key, 'label': cat_map.get(key, key), 'docs': []}
            group_map[key]['docs'].append(doc)
        grouped = [group_map[v] for v, _ in Document.CATEGORY_CHOICES if v in group_map]

    return render(request, 'scripts/document_list.html', {
        'documents': qs,
        'q': q,
        'cat': cat,
        'categories_with_counts': categories_with_counts,
        'total': sum(counts.values()),
        'grouped': grouped,
    })

@login_required
def document_create(request):
    initial = {}
    patient_id = request.GET.get('patient_id') or request.GET.get('patient')
    if patient_id:
        initial['patient'] = patient_id
    form = DocumentForm(request.POST or None, request.FILES or None, initial=initial)
    if form.is_valid():
        document = form.save()
        messages.success(request, f'{document.doc_type} created for {document.patient}.')
        return redirect('document_list')
    return render(request, 'scripts/document_form.html', {'form':form,'title':'New Document'})

@login_required
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk)
    form = DocumentForm(request.POST or None, request.FILES or None, instance=document)
    if form.is_valid():
        form.save()
        messages.success(request, 'Document updated successfully.')
        return redirect('document_detail', pk=pk)
    return render(request, 'scripts/document_form.html', {'form': form, 'title': 'Edit Document'})

@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'scripts/document_detail.html', {'document':document})

@login_required
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        patient_name = str(document.patient)
        doc_type = document.doc_type
        document.delete()
        messages.success(request, f'{doc_type} deleted for {patient_name}.')
        return redirect('document_list')
    return render(request, 'scripts/confirm_delete.html', {'document': document})

@login_required
def document_print(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'scripts/document_print.html', {'document':document})
