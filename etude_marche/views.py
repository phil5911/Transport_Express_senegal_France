import io
import matplotlib
matplotlib.use('Agg')
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



# --------------------
# Formulaire
# --------------------
def questionnaire_view(request):
    if request.method == 'POST':
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('merci')
    else:
        form = QuestionnaireForm()  # pour GET, on crée un formulaire vide

    return render(request, 'etude_marche/questionnaire.html', {'form': form})

def merci_view(request):
    return render(request, 'etude_marche/merci.html')

# --------------------
# Fonction utilitaire pour créer les graphiques
# --------------------
def get_chart_image(series, title, color="#2980B9", show_values=False):
    """
    Crée un graphique sécurisé en barre et retourne l'image en base64.
    Gère :
    - Séries vides ou None
    - Séries numériques ou catégoriques
    - Séries provenant de Counter ou groupby
    """
    # Cas série vide ou None
    if series is None or (isinstance(series, pd.Series) and series.dropna().empty):
        series = pd.Series([0], index=["Aucune donnée"])

    # Si c'est un Counter ou dict, convertir en Series
    if isinstance(series, dict):
        series = pd.Series(series)
    if isinstance(series, Counter):
        series = pd.Series(dict(series))

    # Si c'est un objet ou catégorie, on fait value_counts
    if series.dtype == object or series.dtype.name == "category":
        plot_series = series.value_counts()
    else:
        # Convertir en numérique et remplir les NaN par 0
        plot_series = pd.to_numeric(series, errors='coerce').fillna(0)

    # Cas où plot_series est encore vide
    if plot_series.empty:
        plot_series = pd.Series([0], index=["Aucune donnée"])

    plt.figure(figsize=(4, 2.5))
    plot_series.plot(kind="bar", color=color)
    plt.title(title)
    plt.tight_layout()

    if show_values:
        for i, val in enumerate(plot_series):
            plt.text(i, val, str(round(val, 2)), ha="center", va="bottom", fontsize=8)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

# Wrapper sécurisée pour utiliser get_chart_image
def safe_chart(data, title, color="#3498DB", show_values=False):
    """
    Crée un graphique sous forme d'image Base64 (compatible xhtml2pdf).
    """
    import matplotlib.pyplot as plt
    import io, base64
    import pandas as pd

    if data is None or len(data) == 0:
        return None

    fig, ax = plt.subplots(figsize=(6, 3.5))  # ✅ plus large
    try:
        # Si données numériques -> histogramme
        if pd.api.types.is_numeric_dtype(data):
            data.plot(kind="hist", bins=5, color=color, ax=ax)
        else:
            # Aplatir les listes imbriquées (sécurité)
            if data.apply(lambda x: isinstance(x, list)).any():
                flat = []
                for x in data:
                    if isinstance(x, list):
                        flat.extend(x)
                    else:
                        flat.append(x)
                data = pd.Series(flat)

            plot_series = data.value_counts().sort_values(ascending=False)
            plot_series.plot(kind="bar", color=color, ax=ax)

            if show_values:
                for i, val in enumerate(plot_series):
                    ax.text(i, val + 0.2, str(val), ha="center", va="bottom", fontsize=8)

        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.tick_params(axis='x', labelrotation=45, labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.set_xlabel('')
        ax.set_ylabel('')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)  # ✅ haute résolution pour PDF
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return encoded

    except Exception as e:
        print(f"Erreur safe_chart pour {title}: {e}")
        plt.close(fig)
        return None

# --------------------
# Génération PDF / CSV
# --------------------
def generate_pdf_or_csv(request):
    format_type = request.GET.get("format", "pdf").lower()
    reponses = Questionnaire.objects.all()

    if not reponses.exists():
        return HttpResponse("Aucune donnée disponible pour générer le fichier.")

    df = pd.DataFrame(list(reponses.values(
        'prenom', 'nom', 'age', 'sexe', 'ville', 'email', 'telephone',
        'adresse_postale', 'interet_transport', 'frequence_voyage', 'budget',
        'type_colis', 'services_souhaites', 'moyen_paiement', 'sensibilite_prix'
    )))

    # Colonnes numériques
    numeric_cols = ['frequence_voyage', 'budget']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # ---------------------
    # ✅ 1. Génération Excel
    # ---------------------
    if format_type == "excel":
        wb = Workbook()
        ws = wb.active
        ws.title = "Résultats Étude"

        # Style des en-têtes
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")

        # Ajouter les en-têtes
        for col_num, column_title in enumerate(df.columns, 1):
            cell = ws.cell(row=1, column=col_num, value=column_title)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Ajouter les données
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), 2):
            for c_idx, value in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=value)

        # Ajuster la largeur des colonnes automatiquement
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column].width = min(max_length + 2, 30)

        # Envoi du fichier Excel
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="etude_marche.xlsx"'
        wb.save(response)
        return response

    # ---------------------
    # ✅ 2. Génération CSV
    # ---------------------
    if format_type == "csv":
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="etude_marche.csv"'
        df.to_csv(path_or_buf=response, index=False, sep=';', encoding='utf-8-sig')
        return response

    # ---------------------
    # ✅ 3. Génération PDF
    # ---------------------
    ville_chart = safe_chart(df['ville'] if 'ville' in df.columns else None, "Participants par ville", "#2980B9")
    freq_chart = safe_chart(df['frequence_voyage'] if 'frequence_voyage' in df.columns else None, "Fréquence de voyage", "#27AE60")
    budget_chart = safe_chart(df.groupby('ville')['budget'].mean() if 'ville' in df.columns and 'budget' in df.columns else None, "Budget moyen par ville", "#E67E22")
    type_colis_chart = safe_chart(df['type_colis'] if 'type_colis' in df.columns else None, "Type de colis", "#8E44AD")

    services = []
    if 'services_souhaites' in df.columns:
        for s in df['services_souhaites'].dropna():
            services.extend([x.strip() for x in s.split(',')])
    services_chart = safe_chart(pd.Series(Counter(services)), "Services souhaités", "#D35400", True)
    paiement_chart = safe_chart(df['moyen_paiement'] if 'moyen_paiement' in df.columns else None, "Moyens de paiement", "#16A085")
    sensibilite_chart = safe_chart(df['sensibilite_prix'] if 'sensibilite_prix' in df.columns else None, "Sensibilité au prix", "#C0392B")

    charts_list = [
        ("Participants par ville", ville_chart),
        ("Fréquence de voyage", freq_chart),
        ("Budget moyen par ville", budget_chart),
        ("Type de colis", type_colis_chart),
        ("Services souhaités", services_chart),
        ("Moyens de paiement", paiement_chart),
        ("Sensibilité au prix", sensibilite_chart)
    ]

    context = {
        "projet": "Nio Far Express",
        "clients": 100,
        "date_lancement": "Janvier 2026",
        "villes_depart": ["Aubervilliers", "Montpellier"],
        "villes_arrivee": ["Dakar", "M'bour"],
        "transport_type": "Bagage accompagné",
        "reponses": reponses,
        "charts_list": charts_list,
        "logo_url": "/static/images/logo.png",
    }

    template = get_template("etude_marche/pdf_resume.html")
    html = template.render(context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="etude_marche.pdf"'
    pisa.CreatePDF(html, dest=response, encoding='UTF-8')
    return response

def generate_pdf_resume(request):
    reponses = Questionnaire.objects.all()

    if not reponses.exists():
        return HttpResponse("Aucune donnée disponible pour générer le PDF.")

    context = {
        "projet": "Nio Far Express",
        "clients": 100,
        "date_lancement": "Janvier 2026",
        "villes_depart": ["Aubervilliers", "Montpellier"],
        "villes_arrivee": ["Dakar", "M'bour"],
        "transport_type": "Bagage accompagné",
        "reponses": reponses,
        "logo_url": "https://www.example.com/static/logo.png",  # ou ton chemin static
    }

    template = get_template("etude_marche/pdf_resume.html")
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="resume_etude_marche.pdf"'

    pisa_status = pisa.CreatePDF(
        src=html,
        dest=response,
        encoding='UTF-8'
    )

    if pisa_status.err:
        return HttpResponse(f"Erreur lors de la génération du PDF : {pisa_status.err}")
    return response

# --------------------
# Affichage page plan financement
# --------------------
def plan_financement(request):
    projet = "Nio Far Express"
    transport_type = "Transport par bagage accompagné"
    villes_depart = ["Aubervilliers", "Montpellier"]
    villes_arrivee = ["Dakar", "M'bour"]
    date_lancement = "Janvier 2026"
    clients = 100

    reponses = Questionnaire.objects.all()

    if not reponses.exists():
        df = pd.DataFrame(columns=[
            'prenom', 'nom', 'age', 'sexe', 'ville', 'email', 'telephone', 'adresse_postale',
            'interet_transport', 'frequence_voyage', 'budget', 'type_colis', 'services_souhaites',
            'moyen_paiement', 'sensibilite_prix'
        ])
    else:
        df = pd.DataFrame(list(reponses.values()))
        # Convertir les chaînes de listes en vrais listes pour services_souhaites
        if 'services_souhaites' in df.columns:
            df['services_souhaites'] = df['services_souhaites'].apply(
                lambda x: eval(x) if isinstance(x, str) else x
            )

    # Préparer les données pour les graphiques
    ville_chart = safe_chart(df['ville'] if 'ville' in df.columns else None,
                             "Participants par ville", color="#2980B9")
    freq_chart = safe_chart(df['frequence_voyage'] if 'frequence_voyage' in df.columns else None,
                            "Fréquence de voyage", color="#27AE60")
    budget_chart = safe_chart(
        df.groupby('ville')['budget'].mean() if 'ville' in df.columns and 'budget' in df.columns else None,
        "Budget moyen par ville", color="#E67E22")
    type_colis_chart = safe_chart(df['type_colis'] if 'type_colis' in df.columns else None,
                                  "Type de colis", color="#8E44AD")

    # Services souhaités : transformer en liste aplatie
    services = []
    if 'services_souhaites' in df.columns:
        for s in df['services_souhaites'].dropna():
            if isinstance(s, list):
                services.extend(s)
            elif isinstance(s, str):
                services.extend([x.strip() for x in s.split(',')])
    services_chart = safe_chart(pd.Series(services), "Services souhaités",
                                color="#D35400", show_values=True)

    paiement_chart = safe_chart(df['moyen_paiement'] if 'moyen_paiement' in df.columns else None,
                                "Moyens de paiement", color="#16A085")
    sensibilite_chart = safe_chart(df['sensibilite_prix'] if 'sensibilite_prix' in df.columns else None,
                                   "Sensibilité au prix", color="#C0392B")

    charts_list = [
        ("Participants par ville", ville_chart),
        ("Fréquence de voyage", freq_chart),
        ("Budget moyen par ville", budget_chart),
        ("Type de colis", type_colis_chart),
        ("Services souhaités", services_chart),
        ("Moyens de paiement", paiement_chart),
        ("Sensibilité au prix", sensibilite_chart)
    ]

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
        "budget_chart": budget_chart,
        "type_colis_chart": type_colis_chart,
        "services_chart": services_chart,
        "paiement_chart": paiement_chart,
        "sensibilite_chart": sensibilite_chart,
        "charts_list": charts_list,
        "logo_url": "/static/images/logo.png",
    }

    return render(request, "etude_marche/pdf_resume.html", contexte)







