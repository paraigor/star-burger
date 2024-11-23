from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField("название", max_length=50)
    address = models.CharField(
        "адрес",
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        "контактный телефон",
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = "ресторан"
        verbose_name_plural = "рестораны"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = RestaurantMenuItem.objects.filter(
            availability=True
        ).values_list("product")
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField("название", max_length=50)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        "цена",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    image = models.ImageField("картинка")
    special_status = models.BooleanField(
        "спец.предложение",
        default=False,
        db_index=True,
    )
    description = models.TextField(
        "описание",
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="menu_items",
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="продукт",
    )
    availability = models.BooleanField(
        "в продаже", default=True, db_index=True
    )

    class Meta:
        verbose_name = "пункт меню ресторана"
        verbose_name_plural = "пункты меню ресторана"
        unique_together = [["restaurant", "product"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def fetch_with_total_amounts(self):
        return self.annotate(
            order_amount=Sum(
                F("order_items__price") * F("order_items__quantity")
            )
        )


class Order(models.Model):
    STATUSES = [
        ("accepted", "Принят"),
        ("prepared", "Готовится"),
        ("delivering", "В доставке"),
        ("completed", "Выполнен"),
        ("canceled", "Отменен"),
    ]
    status = models.CharField(
        "Статус заказа",
        max_length=20,
        choices=STATUSES,
        default="accepted",
        db_index=True,
    )
    created_at = models.DateTimeField(
        "Дата/время заказа", default=timezone.now, db_index=True
    )
    firstname = models.CharField("Имя", max_length=200)
    lastname = models.CharField("Фамилия", max_length=200)
    phonenumber = PhoneNumberField("Номер телефона", region="RU")
    called_at = models.DateTimeField(
        "Дата/время звонка", null=True, blank=True, db_index=True
    )
    address = models.TextField("Адрес доставки", max_length=200)
    delivered_at = models.DateTimeField(
        "Дата/время доставки", null=True, blank=True, db_index=True
    )
    comment = models.TextField("Комментарий", blank=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"{self.firstname} {self.lastname} {self.address}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="order_items",
        verbose_name="Заказ",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="продукт",
    )
    quantity = models.PositiveSmallIntegerField("Количество", db_index=True)
    price = models.DecimalField(
        "цена",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0.00,
        db_index=True,
    )

    class Meta:
        verbose_name = "продукт"
        verbose_name_plural = "Состав заказа"

    def __str__(self):
        return f"Заказ {self.order.id} - {self.product.name} - {self.quantity}"
