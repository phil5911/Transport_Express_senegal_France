from django.db import models


class Questionnaire(models.Model):
    prenom = models.CharField(max_length=50)
    nom = models.CharField(max_length=50, null=True, blank=True)
    age = models.IntegerField()
    sexe = models.CharField(max_length=1)
    ville = models.CharField(max_length=50)
    email = models.EmailField(null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    adresse_postale = models.TextField(null=True, blank=True)

    # Questions principales
    interet_transport = models.CharField(max_length=200)
    frequence_voyage = models.IntegerField(null=True, blank=True)  # nombre de voyages / mois
    budget = models.FloatField(null=True, blank=True)               # budget en FCFA

    # Nouvelles colonnes pour les graphiques PDF
    type_colis = models.CharField(max_length=100, null=True, blank=True)
    services_souhaites = models.TextField(null=True, blank=True)
    moyen_paiement = models.CharField(max_length=50, null=True, blank=True)
    sensibilite_prix = models.CharField(max_length=50, null=True, blank=True)

    date_remplissage = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} ({self.ville})"

class PlanFinancement(models.Model):
    nom_projet = models.CharField(max_length=100)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    apport_propre = models.DecimalField(max_digits=12, decimal_places=2)
    financement_banque = models.DecimalField(max_digits=12, decimal_places=2)
    autres_financements = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom_projet

from django.db import models

class Reponse(models.Model):
    # Informations personnelles
    prenom = models.CharField(max_length=50, null=True, blank=True)
    nom = models.CharField(max_length=50, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    sexe = models.CharField(max_length=1, choices=[('M','Homme'),('F','Femme')], null=True, blank=True)
    ville = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    adresse_postale = models.TextField(null=True, blank=True)

    # Questionnaire transport
    interet_transport = models.CharField(max_length=200, null=True, blank=True)
    frequence_voyage = models.IntegerField(null=True, blank=True)
    budget = models.FloatField(null=True, blank=True)
    type_colis = models.CharField(max_length=100, null=True, blank=True)
    services_souhaites = models.TextField(null=True, blank=True)
    moyen_paiement = models.CharField(max_length=50, null=True, blank=True)
    sensibilite_prix = models.CharField(max_length=50, null=True, blank=True)

    # Date de réponse
    date_remplissage = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom or 'Inconnu'} {self.nom or 'Inconnu'} - {self.ville or 'Ville inconnue'}"
