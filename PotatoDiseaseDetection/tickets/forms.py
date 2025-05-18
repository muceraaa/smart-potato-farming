from .models import *
from django import forms

class NewTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['description', 'attachments', 'image_reference']

    def __init__(self, *args, **kwargs):
        print(kwargs)
        user = kwargs.pop('user')  # pop the user from kwargs
        super().__init__(*args, **kwargs)
        self.fields['image_reference'].queryset = UploadedImage.objects.filter(created_by=user)
        self.fields['image_reference'].label = "Use your previously uploaded image"

class TicketMessageForm(forms.ModelForm):
    """
    This form handles logic for messaging in the detail ticket view
    """
    class Meta:
        model = TicketMessage
        fields = ['message']



class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedImage
        fields = ['image']
