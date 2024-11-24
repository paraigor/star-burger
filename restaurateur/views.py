import requests
from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from geopy import distance

from foodcartapp.models import (
    Order,
    Product,
    Restaurant,
    RestaurantMenuItem,
)
from location.models import Location
from star_burger.settings import YAGEO_API_KEY


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(
        base_url,
        params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        },
    )
    response.raise_for_status()
    found_places = response.json()["response"]["GeoObjectCollection"][
        "featureMember"
    ]

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")
    return lat, lon


class Login(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=75,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Укажите имя пользователя",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        max_length=75,
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={"form": form})

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(
            request,
            "login.html",
            context={
                "form": form,
                "ivalid": True,
            },
        )


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("restaurateur:login")


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_products(request):
    restaurants = list(Restaurant.objects.order_by("name"))
    products = list(Product.objects.prefetch_related("menu_items"))

    products_with_restaurant_availability = []
    for product in products:
        availability = {
            item.restaurant_id: item.availability
            for item in product.menu_items.all()
        }
        ordered_availability = [
            availability.get(restaurant.id, False)
            for restaurant in restaurants
        ]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(
        request,
        template_name="products_list.html",
        context={
            "products_with_restaurant_availability": products_with_restaurant_availability,
            "restaurants": restaurants,
        },
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_restaurants(request):
    return render(
        request,
        template_name="restaurants_list.html",
        context={
            "restaurants": Restaurant.objects.all(),
        },
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_orders(request):
    products_in_restaurants = RestaurantMenuItem.objects.filter(
        availability=True
    ).prefetch_related("product")

    restaurants = Restaurant.objects.all()
    restaurants_coords = {}
    for restaurant in restaurants:
        try:
            location = Location.objects.get(address=restaurant.address)
            restaurants_coords[restaurant.name] = (
                location.latitude,
                location.longitude,
            )
        except Location.DoesNotExist:
            try:
                latitude, longitude = fetch_coordinates(
                    YAGEO_API_KEY, restaurant.address
                )
                restaurants_coords[restaurant.name] = (latitude, longitude)
                Location.objects.update_or_create(
                    address=restaurant.address,
                    latitude=latitude,
                    longitude=longitude,
                    defaults={"updated_at": timezone.now},
                )
            except requests.exceptions.HTTPError:
                restaurants_coords[restaurant.name] = None
                continue

    orders = (
        Order.objects.exclude(status__in=["completed", "canceled"])
        .fetch_with_total_amounts()
        .order_by("status")
        .prefetch_related("order_items")
    )

    order_items = []
    for order in orders:
        order_products = [item.product for item in order.order_items.all()]
        restaurants_count = {restaurant: 0 for restaurant in restaurants}

        for product_in_restaurant in products_in_restaurants:
            if product_in_restaurant.product in order_products:
                restaurants_count[product_in_restaurant.restaurant] += 1

        try:
            location = Location.objects.get(address=order.address)
            order_address_coords = (location.latitude, location.longitude)
        except Location.DoesNotExist:
            try:
                latitude, longitude = fetch_coordinates(
                    YAGEO_API_KEY, order.address
                )
                order_address_coords = (latitude, longitude)
                Location.objects.update_or_create(
                    address=order.address,
                    latitude=latitude,
                    longitude=longitude,
                    defaults={"updated_at": timezone.now},
                )
            except requests.exceptions.HTTPError:
                order_address_coords = None

        restaurants_available = {
            restaurant.name: round(
                distance.distance(
                    order_address_coords, restaurants_coords[restaurant.name]
                ).km,
                3,
            )
            for restaurant, count in restaurants_count.items()
            if count == len(order_products)
        }
        restaurants_available_sorted = dict(
            sorted(restaurants_available.items(), key=lambda item: item[1])
        )

        order_items.append(
            {
                "id": order.id,
                "status": order.get_status_display(),
                "payment": order.get_payment_display(),
                "order_amount": order.order_amount,
                "client": f"{order.firstname} {order.lastname}",
                "phonenumber": order.phonenumber,
                "address": order.address,
                "comment": order.comment,
                "restaurants": restaurants_available_sorted,
                "order_restaurant": order.restaurant.name
                if order.restaurant
                else None,
            }
        )

    return render(
        request,
        template_name="order_items.html",
        context={"order_items": order_items},
    )
