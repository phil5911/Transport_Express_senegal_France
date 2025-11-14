<h1>Paiement de la facture 1</h1>
<p>Montant : 60.0 EUR</p>

<form id="payment-form">
  <div id="card-element-container" style="max-width:400px; margin-bottom:10px;">
    <label for="card-element">Carte bancaire</label>
    <div id="card-element" style="border:1px solid #ccc; padding:12px; border-radius:4px; min-height:70px;"></div>
  </div>

  <div id="card-errors" role="alert" style="color:red; margin-bottom:10px;"></div>

  <button type="button" id="pay-button" data-invoice-id="1" style="padding:10px 20px; font-size:16px;">Payer</button>
</form>

<script src="https://js.stripe.com/v3/"></script>
<script defer>
document.addEventListener("DOMContentLoaded", () => {
  // ✅ Ta clé publique Stripe test
  const stripe = Stripe("pk_test_51SRcuoGukqmKcPsGtPDvb2zlu7JFnF7N0fTtLqRlurGzsmk4pYdD1coKPi2sJsQg6M8NBLUyZfnDmneHrWUrBhgT00m9komFZe");
  const elements = stripe.elements();

  // Crée et monte le champ carte
  const card = elements.create('card', { hidePostalCode: true });
  card.mount('#card-element');

  const payButton = document.getElementById('pay-button');
  const cardErrors = document.getElementById('card-errors');

  payButton.addEventListener('click', async () => {
    payButton.disabled = true;
    cardErrors.textContent = "";

    const invoiceId = payButton.dataset.invoiceId;

    try {
      // Appel de ton endpoint Django pour créer le PaymentIntent
      const response = await fetch(`/projet-transport/suivi-colis/payment-intent/${invoiceId}/`);
      const data = await response.json();

      if (data.error) {
        cardErrors.textContent = data.error;
        payButton.disabled = false;
        return;
      }

      const clientSecret = data.client_secret;

      // Confirme le paiement
      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: { card: card }
      });

      if (result.error) {
        cardErrors.textContent = result.error.message;
        payButton.disabled = false;
      } else if (result.paymentIntent.status === 'succeeded') {
        alert("✅ Paiement réussi !");
        window.location.reload(); // ou rediriger vers une page de succès
      }

    } catch (err) {
      console.error(err);
      cardErrors.textContent = "Erreur inattendue.";
      payButton.disabled = false;
    }
  });
});
</script>
