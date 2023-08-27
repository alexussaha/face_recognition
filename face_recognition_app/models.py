from asyncio.windows_events import NULL
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='user_images/')
    face_descriptor = models.BinaryField(default=None)
    
