from django.urls import path
from . import views
from .views import generate_pdf_or_csv

urlpatterns = [
    path('', views.questionnaire_view, name='questionnaire'),
    path('merci/', views.merci_view, name='merci'),
    path('pdf/', views.generate_pdf_resume, name='pdf_resume'),
    path('export/', generate_pdf_or_csv, name='generate_pdf_or_csv'),
    path('plan-financement/', views.plan_financement, name='plan_financement'),
]



