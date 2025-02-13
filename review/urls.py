from django.urls import path
from .views import generate_review, handle_history

urlpatterns = [
    path("review", generate_review, name="generate_review"),
    path("history/<int:history_id>", handle_history, name="handle_history"),
]   