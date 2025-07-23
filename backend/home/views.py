from django.views import generic
from shop.models import Property

class IndexView(generic.TemplateView):
    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["houses"] = Property.objects.filter(is_available=True).order_by('-created_at')
        return context



class ProductView(generic.TemplateView):
    template_name = "home/product.html"
