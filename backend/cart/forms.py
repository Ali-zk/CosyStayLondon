# cart/forms.py
from django import forms
from .models import CartItem, Product

class AddToCartForm(forms.ModelForm):
    """
    فرم برای اضافه کردن محصول به سبد خرید.
    """
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label="محصول")
    quantity = forms.IntegerField(min_value=1, initial=1, label="تعداد")

    class Meta:
        model = CartItem
        fields = ['product', 'quantity']

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            if quantity > product.stock:
                # اگر موجودی کافی نبود، ارور می‌دهد
                self.add_error('quantity', f"فقط {product.stock} عدد از این محصول موجود است.")
        return cleaned_data


class UpdateCartItemForm(forms.ModelForm):
    """
    فرم برای به‌روزرسانی تعداد یک آیتم در سبد خرید.
    """
    quantity = forms.IntegerField(min_value=1, label="تعداد جدید")

    class Meta:
        model = CartItem
        fields = ['quantity']

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        # self.instance به شیء CartItem موجود در دیتابیس اشاره می‌کند
        product = self.instance.product 

        if product and quantity:
            if quantity > product.stock:
                self.add_error('quantity', f"فقط {product.stock} عدد از این محصول موجود است.")
        return cleaned_data