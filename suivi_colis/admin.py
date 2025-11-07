from django.contrib import admin
from .models import Customer, Shipment, Package, TrackingUpdate, Invoice, Payment

admin.site.register(Customer)
admin.site.register(Shipment)
admin.site.register(Package)
admin.site.register(TrackingUpdate)
admin.site.register(Invoice)
admin.site.register(Payment)



