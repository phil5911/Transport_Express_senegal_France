import io
import matplotlib.pyplot as plt
import base64
import csv
from collections import Counter
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .forms import QuestionnaireForm
from .models import Questionnaire, Reponse



# Formulaire
def questionnaire_view(request):
    if request.method == 'POST':
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('merci')
    else:
        form = QuestionnaireForm()
    return render(request, 'etude_marche/questionnaire.html', {'form': form})

def merci_view(request):
    return render(request, 'etude_marche/merci.html')

# --- Fonction utilitaire pour créer les graphiques ---
def get_chart_image(series, title, color="#2980B9", show_values=False):
    """
    Retourne une image base64 pour un graphique pandas ou matplotlib.
    Même si la série est vide, crée un graphique factice.
    """
    if series is None or (isinstance(series, pd.Series) and series.empty):
        series = pd.Series([0], index=["Aucune donnée"])

    plt.figure(figsize=(4, 2.5))
    if series.dtype == object or series.dtype.name == "category":
        series.value_counts().plot(kind="bar", color=color)
    else:
        series.plot(kind="bar", color=color)

    plt.title(title)
    plt.tight_layout()

    if show_values:
        for i, val in enumerate(series.value_counts() if series.dtype == object else series):
            plt.text(i, val, str(round(val, 2)), ha="center", va="bottom", fontsize=8)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

def generate_pdf_or_csv(request):
    """
    Génère PDF ou CSV selon le paramètre ?format=csv
    Protège les graphiques contre les données vides.
    """
    format_type = request.GET.get("format", "pdf").lower()
    reponses = Questionnaire.objects.all()

    if not reponses.exists():
        if format_type == "csv":
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="etude_marche.csv"'
            response.write("Ville;Nb_colis;Montant (€);Type_colis;Services_souhaites;Moyen_paiement;Sensibilite_prix\n")
            return response
        else:
            return HttpResponse("Aucune donnée disponible pour générer le PDF.")

    df = pd.DataFrame(list(reponses.values()))

    # Colonnes numériques
    numeric_cols = ['frequence_voyage', 'budget', 'interet_transport']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if format_type == "csv":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="etude_marche.csv"'
        df.to_csv(path_or_buf=response, index=False, sep=';')
        return response

    # Fonction sécurisée pour créer les charts
    def safe_chart(series, title, color="#2980B9", show_values=False):
        if series is None or (isinstance(series, pd.Series) and series.empty):
            series = pd.Series([0], index=["Aucune donnée"])
        return get_chart_image(series, title, color, show_values)

    # Graphiques
    ville_chart = safe_chart(df['ville'] if 'ville' in df.columns else None, "Participants par ville", "#2980B9")
    freq_chart = safe_chart(df['frequence_voyage'] if 'frequence_voyage' in df.columns else None, "Fréquence de voyage", "#27AE60")
    budget_chart = safe_chart(df.groupby('ville')['budget'].mean() if 'ville' in df.columns and 'budget' in df.columns else None, "Budget moyen par ville", "#E67E22")
    type_colis_chart = safe_chart(df['type_colis'].dropna() if 'type_colis' in df.columns else None, "Type de colis", "#8E44AD")

    services = []
    if 'services_souhaites' in df.columns:
        for s in df['services_souhaites'].dropna():
            services.extend([x.strip() for x in s.split(',')])
    services_chart = safe_chart(pd.Series(Counter(services)), "Services souhaités", "#D35400", True)

    paiement_chart = safe_chart(df['moyen_paiement'].dropna() if 'moyen_paiement' in df.columns else None, "Moyens de paiement", "#16A085", True)
    sensibilite_chart = safe_chart(df['sensibilite_prix'].dropna() if 'sensibilite_prix' in df.columns else None, "Sensibilité au prix", "#C0392B", True)

    context = {
        "projet": "Nio Far Express",
        "clients": 100,
        "date_lancement": "Janvier 2026",
        "villes_depart": ["Aubervilliers", "Montpellier"],
        "villes_arrivee": ["Dakar", "M'bour"],
        "transport_type": "Bagage accompagné",
        "reponses": reponses,
        "ville_chart": ville_chart,
        "freq_chart": freq_chart,
        "budget_chart": budget_chart,
        "type_colis_chart": type_colis_chart,
        "services_chart": services_chart,
        "paiement_chart": paiement_chart,
        "sensibilite_chart": sensibilite_chart,
        "logo_url": "https://www.example.com/static/logo.png",
    }

    template = get_template("etude_marche/plan_financement.html")
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="etude_marche_final.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Erreur lors de la génération du PDF")
    return response

def plan_financement(request):
    projet = "Nio Far Express"
    transport_type = "Transport par bagage accompagné"
    villes_depart = ["Aubervilliers", "Montpellier"]
    villes_arrivee = ["Dakar", "M'bour"]
    date_lancement = "Janvier 2026"
    clients = 100

    reponses = Reponse.objects.all()

    import pandas as pd
    df = pd.DataFrame(list(reponses.values()))
    if not df.empty:
        ville_chart = get_chart_image(df['ville'].value_counts(), 'Participants par ville')
        freq_chart = get_chart_image(df['frequence_voyage'], 'Fréquence de voyage')
        budget_chart = get_chart_image(df['budget'], 'Budget moyen')
    else:
        ville_chart = freq_chart = budget_chart = ''

    contexte = {
        "projet": projet,
        "transport_type": transport_type,
        "villes_depart": villes_depart,
        "villes_arrivee": villes_arrivee,
        "date_lancement": date_lancement,
        "clients": clients,
        "reponses": reponses,
        "ville_chart": ville_chart,
        "freq_chart": freq_chart,
        "budget_chart": budget_chart
    }
    return render(request, "etude_marche/plan_financement.html", contexte)















