from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Ticket)
admin.site.register(TicketMessage)
admin.site.register(UploadedImage)  # Register the UploadedImage model