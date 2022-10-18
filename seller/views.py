from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, ProductCategory


@staff_member_required
def add_json_attrs(request, product_id):
    product = Product.objects.get(id=product_id)
    context = {
        'product': product,
    }
    if request.method == 'POST':
        data = [el for el in request.POST.values()]
        data = tuple(data[1:])
        json_data = dict(data[i:i+2] for i in range(0, len(data), 2))
        print(json_data)
        product.attributes = json_data
        product.save()
        return render(request, 'seller/product/add_json_attrs.html', context)
    return render(request, 'seller/product/add_json_attrs.html', context)
