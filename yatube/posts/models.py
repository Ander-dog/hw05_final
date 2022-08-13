from django.contrib.auth import get_user_model
from django.db import models

from core.models import CustomTextModel, DateTimeModel

User = get_user_model()


class Group(models.Model):

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(DateTimeModel, CustomTextModel):
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True
    )


class Comment(DateTimeModel, CustomTextModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name="unique subscription"),
        ]
