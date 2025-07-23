from django.views.generic import UpdateView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .forms import *
from dashboard.permissions import HasCustomerAccessPermission
from cart.models import Order

    
# Customer Dashboard Home View (already exists, but updated for profile context)
class CustomerDashboardHomeView(LoginRequiredMixin, HasCustomerAccessPermission, TemplateView):
    template_name = 'dashboard/customer/profile.html' # Renamed from home.html for clarity of purpose

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user_obj'] = user
        if hasattr(user, 'profile'):
            context['profile_obj'] = user.profile
        else:
            context['profile_obj'] = None
        return context

# Customer Profile Edit View
class CustomerProfileEditView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, UpdateView):
    model = Profile
    template_name = 'dashboard/customer/edit-profile.html'
    form_class = CustomerProfileEditForm
    success_url = reverse_lazy('dashboard:customer:home') # Assuming 'profile' is the URL for CustomerDashboardHomeView
    success_message = "Your profile has been updated successfully."

    def get_object(self, queryset=None):
        return self.request.user.profile

# Customer Password Change View
class CustomerPasswordChangeView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = 'dashboard/customer/change-password.html'
    form_class = CustomerPasswordChangeForm
    success_url = reverse_lazy('dashboard:customer:change-password') # Redirect back to the same page
    success_message = "Your password has been changed successfully."

# Customer My Bookings List View
class CustomerMyBookingsView(LoginRequiredMixin, HasCustomerAccessPermission, ListView):
    model = Order
    template_name = 'dashboard/customer/my-bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    
# Logout view
class LogoutView(auth_views.LogoutView):
    pass    
