from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q # For search and filter functionality
from django.contrib.auth.decorators import login_required
from .models import Property, Booking # Property and Booking models are required
from .forms import PropertyForm, ProductBookingForm
from django.contrib import messages
from decimal import Decimal # For price calculations
from datetime import timedelta # For calculating number of nights

def product_list(request):
    """
    Display list of houses with search and filter functionality.
    """
    houses = Property.objects.filter(is_available=True).order_by('-created_at')

    # Adding search and filter functionality
    query = request.GET.get('q')
    location = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if query:
        houses = houses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
    if location:
        houses = houses.filter(Q(location__icontains=location) | Q(address__icontains=location))
    if min_price:
        try:
            houses = houses.filter(price_per_night__gte=Decimal(min_price))
        except ValueError:
            messages.error(request, "Please enter the minimum price correctly.")
    if max_price:
        try:
            houses = houses.filter(price_per_night__lte=Decimal(max_price))
        except ValueError:
            messages.error(request, "Please enter the maximum price correctly.")

    return render(request, 'shop/product.html', {'houses': houses})

# Product detail view
def product_detail(request, pk):
    """
    Display property details and process booking form to add to cart (via session).
    """
    house = get_object_or_404(Property, pk=pk)
    images = house.images.all
    
    if request.method == 'POST':
        # Use ProductBookingForm to validate input
        booking_form = ProductBookingForm(request.POST)
        if booking_form.is_valid():
            check_in_date = booking_form.cleaned_data['check_in_date']
            check_out_date = booking_form.cleaned_data['check_out_date']
            number_of_guests = booking_form.cleaned_data['number_of_guests']
            full_name = booking_form.cleaned_data['full_name']
            email = booking_form.cleaned_data['email']
            phone_number = booking_form.cleaned_data.get('phone_number') # Phone number can be null

            # Store information in session
            request.session['temp_booking_data'] = {
                'property_id': house.pk,
                'check_in_date': str(check_in_date), # Convert to string for session
                'check_out_date': str(check_out_date), # Convert to string for session
                'number_of_guests': number_of_guests,
                'full_name': full_name,
                'email': email,
                'phone_number': phone_number,
                'price_at_addition': str(house.price_per_night), # Current property price (as string)
            }
            request.session.modified = True # Ensure session changes are saved
            
            messages.info(request, 'Reservation information is being transferred to your shopping cart')
            # Redirect to the cart app view to process session data and save to database
            return redirect('cart:add_from_session')
        else:
            # If form is not valid, errors will be available in booking_form.errors
            messages.error(request, 'Please Enter valid information.')
    else:
        # Initialize form with current property_id and user details if authenticated
        booking_form = ProductBookingForm(initial={
            'property': house.pk,
            'full_name': request.user.email if request.user.is_authenticated else '',
            'email': request.user.email if request.user.is_authenticated else ''
        })

    context = {
        'house': house,
        'images': images,
        'booking_form': booking_form,
    }
    return render(request, 'shop/product_detail.html', context)

# add property view
@login_required
def add_property_view(request):
    """
    Allow logged-in users to add new properties.
    """
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES) # Adding request.FILES for image upload
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            messages.success(request, 'Your property has been successfully added.')
            return redirect('shop:product_detail', pk=property_obj.pk)
        else:
            messages.error(request, 'Error adding property. Please check the form.')
    else:
        form = PropertyForm()
    return render(request, 'shop/add_property.html', {'form': form})
