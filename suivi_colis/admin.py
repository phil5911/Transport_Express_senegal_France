from django.contrib import admin
from .models import Customer, Shipment, Package, TrackingUpdate, Invoice, Payment

admin.site.register(Customer)
admin.site.register(Package)
admin.site.register(TrackingUpdate)
admin.site.register(Invoice)
admin.site.register(Payment)

# Enregistrement avec personnalisation pour Shipment
@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer', 'status', 'origin', 'destination',
                    'sender_name', 'receiver_name')
    fields = ('customer', 'name', 'origin', 'destination', 'status',
              'sender_name', 'sender_email', 'sender_address',
              'receiver_name', 'receiver_email', 'receiver_address',
              'tracking_number')

