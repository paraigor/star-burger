from django.db import transaction
from rest_framework.serializers import ModelSerializer

from .models import Order, OrderItem


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(
        many=True, allow_empty=False, write_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "firstname",
            "lastname",
            "phonenumber",
            "address",
            "products",
        ]

    @transaction.atomic
    def create(self, validated_data):
        order = Order.objects.create(
            firstname=validated_data["firstname"],
            lastname=validated_data["lastname"],
            phonenumber=validated_data["phonenumber"],
            address=validated_data["address"],
        )

        order_items = []
        for order_item in validated_data["products"]:
            order_items.append(
                OrderItem(
                    order=order,
                    product=order_item["product"],
                    quantity=order_item["quantity"],
                    price=order_item["product"].price,
                )
            )
        OrderItem.objects.bulk_create(order_items)
        return order
