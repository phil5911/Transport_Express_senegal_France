from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from .models import Shipment, Package, TrackingUpdate, Invoice, Payment, Customer
from .forms import ShipmentCreateForm, PackageForm
from django.template.loader import render_to_string
import stripe
from django.conf import settings
from xhtml2pdf import pisa
import io
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def dashboard(request):
    # si le Customer n'existe pas, on le crée automatiquement (optionnel)
    customer, _ = Customer.objects.get_or_create(user=request.user)
    shipments = customer.shipments.all().order_by('-created_at')
    return render(request, 'suivi_colis/dashboard.html', {'shipments': shipments})

@login_required
def shipment_detail(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk, customer__user=request.user)
    return render(request, 'suivi_colis/shipment_detail.html', {'shipment': shipment})

@login_required
def create_shipment(request):
    customer = Customer.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        form = ShipmentCreateForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.customer = customer
            s.status = 'created'
            s.save()
            return redirect('suivi_colis:shipment_detail', pk=s.pk)
    else:
        form = ShipmentCreateForm()
    return render(request, 'suivi_colis/create_shipment.html', {'form': form})

@login_required
def add_package(request, shipment_pk):
    shipment = get_object_or_404(Shipment, pk=shipment_pk, customer__user=request.user)
    if request.method == 'POST':
        form = PackageForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.shipment = shipment
            p.save()
            return redirect('suivi_colis:shipment_detail', pk=shipment.pk)
    else:
        form = PackageForm()
    return render(request, 'suivi_colis/add_package.html', {'form': form, 'shipment': shipment})

@login_required
def invoice_pdf(request, shipment_pk):
    shipment = get_object_or_404(Shipment, pk=shipment_pk, customer__user=request.user)
    invoice = getattr(shipment, 'invoice', None)
    if not invoice:
        return HttpResponse("Facture introuvable", status=404)
    html = render_to_string('suivi_colis/invoice.html', {'invoice': invoice, 'shipment': shipment})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Erreur génération PDF", status=500)
    return response

@login_required
def create_payment_intent(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk, shipment__customer__user=request.user)
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(invoice.amount * 100),
            currency=invoice.currency.lower(),
            metadata={'invoice_id': invoice.pk, 'invoice_number': invoice.invoice_number},
        )
        Payment.objects.create(invoice=invoice, stripe_payment_intent=intent['id'], amount=invoice.amount, currency=invoice.currency, status='pending')
        return JsonResponse({'client_secret': intent['client_secret']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def test_payment(request):
    try:
        intent = stripe.PaymentIntent.create(amount=5000, currency='eur', metadata={'test': 'true'})
        return render(request, 'suivi_colis/test_payment.html', {
            'client_secret': intent.client_secret,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponseBadRequest()
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest()

    if event['type'] == 'payment_intent.succeeded':
        pi = event['data']['object']
        intent_id = pi.get('id')
        payment = Payment.objects.filter(stripe_payment_intent=intent_id).first()
        if payment:
            payment.status = 'succeeded'
            payment.save()
            invoice = payment.invoice
            invoice.paid = True
            invoice.paid_at = timezone.now()
            invoice.save()
    return HttpResponse(status=200)

