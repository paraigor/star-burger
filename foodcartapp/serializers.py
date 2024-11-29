import requests
from django.db import transaction
from django.utils import timezone
from rest_framework.serializers import ModelSerializer

from location.models import Location
from restaurateur.tools import fetch_coordinates
from star_burger.settings import YAGEO_API_KEY

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
        address = validated_data["address"]
        order = Order.objects.create(
            firstname=validated_data["firstname"],
            lastname=validated_data["lastname"],
            phonenumber=validated_data["phonenumber"],
            address=address,
        )

        try:
            Location.objects.get(address=address)
        except Location.DoesNotExist:
            try:
                latitude, longitude = fetch_coordinates(
                    YAGEO_API_KEY, address
                )

                Location.objects.update_or_create(
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                    defaults={"updated_at": timezone.now},
                )
            except requests.exceptions.HTTPError:
                Location.objects.create(
                    address=address,
                    defaults={"updated_at": timezone.now},
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
