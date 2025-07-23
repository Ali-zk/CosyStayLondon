from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from shop.models import Property, PropertyImage
from .forms import PropertyForm, PropertyImageForm, PropertyImageFormSet

def property_list(request):
    properties = Property.objects.all()
    return render(request, 'dashboard/admin/properties/property_list.html', {'properties': properties})

def property_create(request):
    form = PropertyForm(request.POST or None, request.FILES or None)
    formset = PropertyImageFormSet(request.POST or None, request.FILES or None, instance=Property())

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            property_instance = form.save()
            formset = PropertyImageFormSet(request.POST, request.FILES, instance=property_instance)
            if formset.is_valid():
                formset.save()
                return redirect('dashboard:admin:property:property_list')
            else:
                pass
    
    context = {
        'form': form,
        'formset': formset,
        'page_title': 'Add New Property'
    }
    return render(request, 'dashboard/admin/property/property_form.html', context)

def property_update(request, pk):
    property_instance = get_object_or_404(Property, pk=pk)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=property_instance)
    formset = PropertyImageFormSet(request.POST or None, request.FILES or None, instance=property_instance)

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('dashboard:admin:property:property_list')
    
    context = {
        'form': form,
        'formset': formset,
        'property': property_instance,
        'page_title': 'Update Property'
    }
    return render(request, 'dashboard/admin/property/property_form.html', context)

def property_delete(request, pk):
    property_instance = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        property_instance.delete()
        return redirect('dashboard:admin:property:property_list')
    return render(request, 'dashboard/admin/property/property_confirm_delete.html', {'property': property_instance, 'page_title': 'Delete Property'})