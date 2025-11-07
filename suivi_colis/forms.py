from django import forms
from .models import Shipment, Package

class ShipmentCreateForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['name', 'origin', 'destination']

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['type_colis', 'weight_kg', 'length_cm', 'width_cm', 'height_cm', 'declared_value']
