from django.urls import path
from .views import generate_review, handle_history, get_histories

urlpatterns = [
    path("review", generate_review, name="generate_review"),
    path("histories/<int:user_id>", get_histories, name="get_histories"),
    path("history/<int:history_id>", handle_history, name="handle_history"),
]   