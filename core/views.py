from django.shortcuts import render
from django.db.models import Count
from .models import LampioneManutenzione

# Create your views here.
def home(request):
    # QUERY: SELECT tcs_descr, COUNT(*) as totale 
    #        FROM core_lampionemanutenzione 
    #        GROUP BY tcs_descr 
    #        ORDER BY totale DESC LIMIT 5
    
    top_5_motivi = (
        LampioneManutenzione.objects
        .values('tcs_descr')                  # Raggruppa per descrizione guasto
        .annotate(totale=Count('id'))         # Conta quanti ID ci sono per gruppo
        .order_by('-totale')                  # Ordina decrescente (dal più alto)
        .exclude(tcs_descr__isnull=True)      # Escludi i nulli (pulizia dati)
        [:5]                                  # Prendi solo i primi 5 (LIMIT 5)
    )

    context = {
        'top_5_motivi': top_5_motivi
    }
    return render(request, 'core/home.html', context)