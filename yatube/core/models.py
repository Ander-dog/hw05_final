from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class DateTimeModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-created']


class CustomTextModel(models.Model):
    """Абстрактная модель. Добавляет текст и автора."""
    text = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.text[:15]
