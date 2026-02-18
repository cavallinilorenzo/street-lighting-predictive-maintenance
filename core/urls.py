from django.contrib import admin
from django.urls import path
from core import views # Importa le views dal tuo modulo core

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Percorso per la Home
    path('', views.home, name='home'), 
    
    # Percorso per la Mappa
    path('mappa/', views.mappa_lampioni, name='mappa_lampioni'), 
]