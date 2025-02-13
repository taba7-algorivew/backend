from django.urls import path
from .views import generate_review, handle_history, get_histories, get_history

urlpatterns = [
    path("review", generate_review, name="generate_review"),
    path("histories/<int:user_id>", get_histories, name="get_histories"),
    path("histories/<int:review_id>", get_history, name="get_history"),
    path("history/<int:history_id>", handle_history, name="handle_history"),
]   