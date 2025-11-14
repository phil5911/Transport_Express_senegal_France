from django.urls import path
from . import views

app_name = 'suivi_colis'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_shipment, name='create_shipment'),
    path('shipment/<int:pk>/', views.shipment_detail, name='shipment_detail'),
    path('shipment/<int:shipment_pk>/add-package/', views.add_package, name='add_package'),
    path('invoice/<int:shipment_pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('payment/<int:invoice_pk>/', views.payment_page, name='payment_page'),
    path('payment-intent/<int:invoice_pk>/', views.create_payment_intent, name='create_payment_intent'),
    path('test-payment/', views.test_payment, name='test_payment'),
    path('test-payment/<int:invoice_pk>/', views.test_payment, name='test_payment'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('test-email/', views.test_email, name='test_email'),
]
