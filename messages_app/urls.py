from django.urls import path
from . import views

urlpatterns = [
    path('misused-senders/', views.find_misused_sender_ids, name='misused_senders'),
]

