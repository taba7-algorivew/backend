from django.urls import path
from .views import (
    chatbot,
    generate_review,
    get_histories, 
    get_history,
    get_solution,
    handle_history, 
    handle_problem,
)

urlpatterns = [
    path("chatbot", chatbot, name="chatbot"),
    path("review", generate_review, name="generate_review"),
    path("user-histories/<int:user_id>", get_histories, name="get_histories"),
    path("histories/<int:history_id>", get_history, name="get_history"),
    path("histories/<int:review_id>", get_history, name="get_history"),
    path("solution/<int:history_id>", get_solution, name="get_solution"),
    path("history/<int:history_id>", handle_history, name="handle_history"),
    path("problem/<int:problem_id>", handle_problem, name="handle_problem"),
]   