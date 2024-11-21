import phonenumbers as ph
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderItem, Product


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse(
        [
            {
                "title": "Burger",
                "src": static("burger.jpg"),
                "text": "Tasty Burger at your door step",
            },
            {
                "title": "Spices",
                "src": static("food.jpg"),
                "text": "All Cuisines",
            },
            {
                "title": "New York",
                "src": static("tasty.jpg"),
                "text": "Food is incomplete without a tasty dessert",
            },
        ],
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


def product_list_api(request):
    products = Product.objects.select_related("category").available()

    dumped_products = []
    for product in products:
        dumped_product = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "special_status": product.special_status,
            "description": product.description,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
            }
            if product.category
            else None,
            "image": product.image.url,
            "restaurant": {
                "id": product.id,
                "name": product.name,
            },
        }
        dumped_products.append(dumped_product)
    return JsonResponse(
        dumped_products,
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


@api_view(["POST"])
def register_order(request):
    site_order = request.data
    if not site_order.get("products") or not isinstance(
        site_order["products"], list
    ):
        return Response({"error": "products not present or not a list"})
    for order_product in site_order["products"]:
        order_product_id = order_product["product"]
        product = Product.objects.filter(pk=order_product_id)
        if not product:
            return Response({"error": "product id not valid"})
    if not site_order.get("firstname") or not isinstance(
        site_order["firstname"], str
    ):
        return Response({"error": "firstname not present or not a string"})
    if not site_order.get("lastname") or not isinstance(
        site_order["lastname"], str
    ):
        return Response({"error": "lastname not present or not a string"})
    if not site_order.get("phonenumber") or not isinstance(
        site_order["phonenumber"], str
    ):
        return Response({"error": "phonenumber not present or not a string"})
    try:
        phone_number = ph.parse(site_order.get("phonenumber"), "RU")
        if not ph.is_valid_number(phone_number):
            raise
    except Exception:
        return Response({"error": "phonenumber not valid"})

    if not site_order.get("address") or not isinstance(
        site_order["address"], str
    ):
        return Response({"error": "address not present or not a string"})

    order = Order.objects.create(
        first_name=site_order["firstname"],
        last_name=site_order["lastname"],
        phone_number=site_order["phonenumber"],
        delivery_address=site_order["address"],
    )

    for order_product in site_order["products"]:
        order_product_id = order_product["product"]
        product = Product.objects.get(pk=order_product_id)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=order_product["quantity"],
        )

    return Response(site_order)
