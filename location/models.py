from django.db import models


class Location(models.Model):
    address = models.TextField("Адрес места", max_length=200)
    latitude = models.FloatField("Широта")
    longitude = models.FloatField("Долгота")
    updated_at = models.DateTimeField(
        "Дата/время обновления", null=True, blank=True, db_index=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["address", "latitude", "longitude"],
                name="unigue_location_coordinates",
            ),
        ]
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def __str__(self):
        return f"{self.latitude},{self.longitude} {self.address}"
