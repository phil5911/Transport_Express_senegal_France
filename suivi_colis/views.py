import io
import stripe
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from .models import Shipment, Package, TrackingUpdate, Invoice, Payment, Customer
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import ShipmentCreateForm, PackageForm
from django.template.loader import render_to_string
from xhtml2pdf import pisa




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
def payment_page(request, invoice_pk):
    # Récupère la facture pour l'utilisateur connecté
    invoice = get_object_or_404(Invoice, pk=invoice_pk, shipment__customer__user=request.user)

    # Crée un PaymentIntent pour Stripe
    intent = stripe.PaymentIntent.create(
        amount=int(invoice.amount * 100),  # montant en centimes
        currency=invoice.currency.lower(),
        metadata={'invoice_id': invoice.pk, 'invoice_number': invoice.invoice_number},
    )

    return render(request, 'suivi_colis/payment_page.html', {
        'invoice': invoice,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': intent.client_secret,
    })
@login_required
def test_payment(request, invoice_pk):
    try:
        intent = stripe.PaymentIntent.create(amount=5000, currency='eur', metadata={'test': 'true'})
        return render(request, 'suivi_colis/test_payment.html', {
            'client_secret': intent.client_secret,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/projet-transport/suivi-colis/')  # ✅ redirige vers le tableau de bord
        else:
            messages.error(request, 'Nom d’utilisateur ou mot de passe invalide.')
    return render(request, 'suivi_colis/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('suivi_colis:login')

@login_required(login_url='/projet-transport/login/')
def dashboard(request):
    return render(request, 'suivi_colis/dashboard.html')
@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)  # GET non autorisé

    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    print("Webhook reçu !")
    print("Payload brut:", payload)

    try:
        # Stripe attend du texte UTF-8
        event = stripe.Webhook.construct_event(
            payload=payload.decode("utf-8"),
            sig_header=sig_header,
            secret=endpoint_secret
        )
        print("Événement construit :", event)

    except ValueError:
        print("❌ Payload invalide")
        return HttpResponseBadRequest("Invalid payload")

    except stripe.error.SignatureVerificationError as e:
        print("❌ Signature Stripe invalide !", e)
        return HttpResponseBadRequest("Invalid signature")

    # -------------------------------
    # TRAITEMENT DES ÉVÉNEMENTS STRIPE
    # -------------------------------
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        intent_id = data.get("id")
        print("💰 Paiement réussi :", intent_id)

        payment = Payment.objects.filter(stripe_payment_intent=intent_id).first()

        if payment:
            payment.status = "succeeded"
            payment.save()

            # Marquer la facture comme payée
            invoice = payment.invoice
            invoice.paid = True
            invoice.paid_at = timezone.now()
            invoice.save()

            print("🧾 Facture marquée comme payée")

    elif event_type == "payment_intent.payment_failed":
        intent_id = data.get("id")
        print("❌ Paiement échoué :", intent_id)

        payment = Payment.objects.filter(stripe_payment_intent=intent_id).first()
        if payment:
            payment.status = "failed"
            payment.save()

    # Stripe doit recevoir un 200 sinon il renvoie l'événement
    return HttpResponse(status=200)

def test_email(request):
    try:
        send_mail(
            subject="Test Django Email ✅",
            message="Ceci est un email de test envoyé depuis Django.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["ton.email@gmail.com"],  # ton email de réception
            fail_silently=False,
        )
        return HttpResponse("Email envoyé avec succès !")
    except Exception as e:
        return HttpResponse(f"Erreur lors de l’envoi de l’email : {e}")





