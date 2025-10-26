from django import forms
from .models import Questionnaire, PlanFinancement


from django import forms
from .models import Questionnaire

SERVICES_CHOICES = [
    ('retrait_domicile', 'Retrait à domicile'),
    ('livraison_rapide', 'Livraison rapide'),
    ('assurance', 'Assurance colis'),
]

class QuestionnaireForm(forms.ModelForm):
    services_souhaites = forms.MultipleChoiceField(
        choices=SERVICES_CHOICES,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Questionnaire
        fields = [
            'prenom',
            'age',
            'sexe',
            'ville',
            'interet_transport',
            'frequence_voyage',
            'budget',
            'type_colis',
            'services_souhaites',
            'moyen_paiement',
            'sensibilite_prix',
        ]
        widgets = {
            'type_colis': forms.RadioSelect(choices=[('petit','Petit'),('moyen','Moyen'),('grand','Grand')]),
            'moyen_paiement': forms.RadioSelect(choices=[('cash','Cash'),('mobile','Mobile Money'),('carte','Carte bancaire')]),
            'sensibilite_prix': forms.RadioSelect(choices=[('haute','Haute'),('moyenne','Moyenne'),('faible','Faible')]),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(choices=[('M','Homme'),('F','Femme')], attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'interet_transport': forms.TextInput(attrs={'class': 'form-control'}),
            'frequence_voyage': forms.NumberInput(attrs={'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PlanFinancementForm(forms.ModelForm):
    class Meta:
        model = PlanFinancement
        fields = ['nom_projet', 'montant_total', 'apport_propre', 'financement_banque', 'autres_financements']
