from django.views.generic import (
    View, TemplateView, ListView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView

from accounts.models import UserType, User, Profile
from shop.models import Property, PropertyImage
from cart.models import Cart, CartItem, Order, OrderItem

# Permissions and Forms
from dashboard.permissions import HasAdminAccessPermission
from dashboard.admin.forms import AdminPasswordChangeForm, UserProfileCreationForm, UserProfileChangeForm, MyProfileForm # Assuming these are defined in dashboard.admin.forms

from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views as auth_views
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


# Home view
class AdminDashboardHomeView(LoginRequiredMixin, HasAdminAccessPermission, TemplateView):
    template_name = 'dashboard/admin/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Date Range for Comparisons ---
        today = timezone.now().date()
        # Adjust 'days' for 'last month' as needed, or calculate actual month start/end
        one_month_ago = today - timedelta(days=30)

        # --- Dynamic Dashboard Cards ---

        # Total Orders
        total_orders = Order.objects.count()
        context["total_orders"] = total_orders

        # Total Orders Last Month for comparison
        total_orders_last_month = Order.objects.filter(created_at__gte=one_month_ago).count()
        if total_orders_last_month > 0:
            order_growth_percent = ((total_orders - total_orders_last_month) / total_orders_last_month) * 100
            context["total_orders_growth_percent"] = f"{order_growth_percent:.0f}%"
            context["total_orders_growth_status"] = "increase" if order_growth_percent >= 0 else "decrease"
        else:
            context["total_orders_growth_percent"] = "N/A" # No previous orders to compare
            context["total_orders_growth_status"] = "neutral"

        # Listed Properties (Total)
        context["total_properties"] = Property.objects.count()

        # New Properties (e.g., added in the last month)
        new_properties_this_month = Property.objects.filter(created_at__gte=one_month_ago).count()
        context["new_properties_this_month"] = new_properties_this_month


        # New Users
        total_users = User.objects.count()
        context["total_users"] = total_users
        new_users_this_month = User.objects.filter(created_date__gte=one_month_ago).count()
        context["new_users_this_month"] = new_users_this_month

        if (total_users - new_users_this_month) > 0:
            user_growth_percent = (new_users_this_month / (total_users - new_users_this_month)) * 100
            context["user_growth_percent"] = f"{user_growth_percent:.0f}%"
            context["user_growth_status"] = "increase" if user_growth_percent >= 0 else "neutral"
        else:
            context["user_growth_percent"] = "N/A"
            context["user_growth_status"] = "neutral"

        # Total Revenue
        total_revenue = Order.objects.filter(status__in=['confirmed', 'completed']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        context["total_revenue"] = total_revenue

        revenue_last_month = Order.objects.filter(
            status__in=['confirmed', 'completed'],
            created_at__gte=one_month_ago
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

        if revenue_last_month > 0:
            revenue_growth_percent = ((total_revenue - revenue_last_month) / revenue_last_month) * 100
            context["revenue_growth_percent"] = f"{revenue_growth_percent:.0f}%"
            context["revenue_growth_status"] = "increase" if revenue_growth_percent >= 0 else "decrease"
        else:
            context["revenue_growth_percent"] = "N/A"
            context["revenue_growth_status"] = "neutral"

        # Recent Orders
        context["recent_orders"] = Order.objects.all().order_by('-created_at')[:5]

        # Sales Chart Data (for Chart.js)
        today = timezone.now().date()
        chart_labels = []
        chart_data = []
        for i in range(5, -1, -1): # Iterate from 5 months ago down to 0 months ago
            month = today - timedelta(days=30 * i) # Approximation of a month
            start_of_month = month.replace(day=1)
            if start_of_month.month == 12:
                end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)

            monthly_revenue = Order.objects.filter(
                status__in=['confirmed', 'completed'],
                created_at__range=(start_of_month, end_of_month + timedelta(days=1))
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

            chart_labels.append(month.strftime("%b %Y"))
            chart_data.append(float(monthly_revenue))

        context["sales_chart_labels"] = chart_labels
        context["sales_chart_data"] = chart_data

        return context

# Logout View
class LogoutView(LogoutView):
    pass

# Admin Security Edit View
class AdminSecurityEditView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = 'dashboard/admin/security-edit.html'
    form_class = AdminPasswordChangeForm
    success_url = reverse_lazy('dashboard:admin:security-edit')
    success_message = 'Your password has been updated successfully.'


# =================== Property Management ===================

class AdminPropertyListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    template_name = 'dashboard/admin/properties/property_list.html'
    context_object_name = 'properties'
    model = Property
    paginate_by = 10
    


class AdminPropertyCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    model = Property
    template_name = 'dashboard/admin/properties/property_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:property-list')
    success_message = "New property created successfully."

class AdminPropertyUpdateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    model = Property
    template_name = 'dashboard/admin/properties/property_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:property-list')
    success_message = "Property updated successfully."

class AdminPropertyDeleteView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, DeleteView):
    model = Property
    template_name = 'dashboard/admin/properties/property_confirm_delete.html'
    success_url = reverse_lazy('dashboard:admin:property-list')
    success_message = "Property deleted successfully."


# =================== Cart Management ===================

class AdminCartListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    model = Cart
    template_name = 'dashboard/admin/carts/cart_list.html'
    context_object_name = 'carts'
    paginate_by = 10

# Create and Update views for Cart are usually managed manually, but added as per your request
class AdminCartCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    model = Cart
    template_name = 'dashboard/admin/carts/cart_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:cart-list')
    success_message = "New cart created successfully."

class AdminCartUpdateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    model = Cart
    template_name = 'dashboard/admin/carts/cart_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:cart-list')
    success_message = "Cart updated successfully."

class AdminCartDeleteView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, DeleteView):
    model = Cart
    template_name = 'dashboard/admin/carts/cart_confirm_delete.html'
    success_url = reverse_lazy('dashboard:admin:cart-list')
    success_message = "Cart deleted successfully."


# =================== CartItem Management ===================

class AdminCartItemListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    model = CartItem
    template_name = 'dashboard/admin/cartitems/cartitem_list.html'
    context_object_name = 'cartitems'
    paginate_by = 10

class AdminCartItemCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    model = CartItem
    template_name = 'dashboard/admin/cartitems/cartitem_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:cartitem-list')
    success_message = "New cart item created successfully."

class AdminCartItemUpdateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    model = CartItem
    template_name = 'dashboard/admin/cartitems/cartitem_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:cartitem-list')
    success_message = "Cart item updated successfully."

class AdminCartItemDeleteView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, DeleteView):
    model = CartItem
    template_name = 'dashboard/admin/cartitems/cartitem_confirm_delete.html'
    success_url = reverse_lazy('dashboard:admin:cartitem-list')
    success_message = "Cart item deleted successfully."


# =================================================================
# === New Code for Order, OrderItem, User ===
# =================================================================

# =================== Order Management ===================

class AdminOrderListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    model = Order
    template_name = 'dashboard/admin/orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

class AdminOrderCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    model = Order
    template_name = 'dashboard/admin/orders/order_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:order-list')
    success_message = "New order created successfully."

class AdminOrderUpdateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    model = Order
    template_name = 'dashboard/admin/orders/order_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:order-list')
    success_message = "Order updated successfully."

class AdminOrderDeleteView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, DeleteView):
    model = Order
    template_name = 'dashboard/admin/orders/order_confirm_delete.html'
    success_url = reverse_lazy('dashboard:admin:order-list')
    success_message = "Order deleted successfully."


# =================== OrderItem Management ===================

class AdminOrderItemListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    model = OrderItem
    template_name = 'dashboard/admin/orderitems/orderitem_list.html'
    context_object_name = 'orderitems'
    paginate_by = 10

class AdminOrderItemCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    model = OrderItem
    template_name = 'dashboard/admin/orderitems/orderitem_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:orderitem-list')
    success_message = "New order item created successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["properties"] = Property.objects.filter(is_available=1)
        context["orders"] = Order.objects.all()
        return context


class AdminOrderItemUpdateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    model = OrderItem
    template_name = 'dashboard/admin/orderitems/orderitem_form.html'
    fields = '__all__'
    success_url = reverse_lazy('dashboard:admin:orderitem-list')
    success_message = "Order item updated successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["properties"] = Property.objects.filter(is_available=1)
        context["orders"] = Order.objects.all()
        return context

class AdminOrderItemDeleteView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, DeleteView):
    model = OrderItem
    template_name = 'dashboard/admin/orderitems/orderitem_confirm_delete.html'
    success_url = reverse_lazy('dashboard:admin:orderitem-list')
    success_message = "Order item deleted successfully."


# =================== User Management ===================

class AdminUserListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    model = User
    template_name = 'dashboard/admin/users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

class AdminUserCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    template_name = 'dashboard/admin/users/user_form.html'
    form_class = UserProfileCreationForm
    success_url = reverse_lazy('dashboard:admin:user-list')
    success_message = "New user and profile created successfully. (Password must be set via Django admin for new users)"

class AdminUserUpdateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'dashboard/admin/users/user_form.html'
    form_class = UserProfileChangeForm
    success_url = reverse_lazy('dashboard:admin:user-list')
    success_message = "User and profile information updated successfully."

class AdminUserDeleteView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, DeleteView):
    model = User
    template_name = 'dashboard/admin/users/user_confirm_delete.html'
    success_url = reverse_lazy('dashboard:admin:user-list')
    success_message = "User deleted successfully."


class AdminProfileUpdateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    model = Profile
    template_name = 'dashboard/admin/profile_admin.html'
    form_class = MyProfileForm
    success_url = reverse_lazy('dashboard:admin:profile')
    success_message = "Your profile has been updated successfully."

    def get_object(self, queryset=None):
        return self.request.user.profile

    # You might also want to override form_valid to handle image uploads if necessary
    # def form_valid(self, form):
    #     response = super().form_valid(form)
    #     # Any additional logic after profile is saved
    #     return response