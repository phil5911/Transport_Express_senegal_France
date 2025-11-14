import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def generate_reference():
    return f"REF-{uuid.uuid4().hex[:10].upper()}"

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('created', 'Créé'),
        ('in_transit', 'En cours'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    ]

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='shipments')

    # Référence unique générée automatiquement
    reference = models.CharField(max_length=64, unique=True, editable=False, default=generate_reference)

    name = models.CharField(max_length=200, help_text="Titre / description")
    origin = models.CharField(max_length=200, blank=True)
    destination = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')

    # Informations expéditeur
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_email = models.EmailField(blank=True, null=True)
    sender_address = models.CharField(max_length=500, blank=True, null=True)

    # Informations destinataire
    receiver_name = models.CharField(max_length=255, blank=True, null=True)
    receiver_email = models.EmailField(blank=True, null=True)
    receiver_address = models.CharField(max_length=500, blank=True, null=True)

    # Numéro de suivi optionnel
    tracking_number = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Génère automatiquement une référence si absente
        if not self.reference:
            self.reference = f"REF-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.name}"


class Package(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='packages')
    type_colis = models.CharField(max_length=100, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    length_cm = models.FloatField(null=True, blank=True)
    width_cm = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    declared_value = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Colis {self.id} - {self.type_colis or '—'}"

class TrackingUpdate(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='tracking_updates')
    status = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.status} @ {self.created_at}"

class Invoice(models.Model):
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default='EUR')
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"INV-{self.invoice_number}"

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    stripe_payment_intent = models.CharField(max_length=200, blank=True, null=True)
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default='EUR')
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"






