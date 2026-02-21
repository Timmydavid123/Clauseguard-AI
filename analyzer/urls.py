from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('results/', views.results, name='results'),
    path('api/analyze-pdf/', views.analyze_pdf, name='analyze_pdf'),
    path('api/analyze-text/', views.analyze_text, name='analyze_text'),
]
