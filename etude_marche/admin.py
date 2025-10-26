from django.contrib import admin
from .models import Questionnaire

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'age', 'sexe', 'ville', 'date_remplissage')
    list_filter = ('ville', 'sexe', 'type_colis', 'moyen_paiement')
    search_fields = ('prenom', 'ville')



