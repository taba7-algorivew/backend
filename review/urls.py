from django.urls import path
from .views import (
    generate_review, 
    handle_history, 
    get_histories, 
    get_history, 
    chatbot, 
    solution_view,
    handle_problem, 
    hello_algoreview,
    get_first_review,
)

urlpatterns = [
    path("api", hello_algoreview, name="hello_algoreview"),
    path("chatbot", chatbot, name="chatbot"),
    path("review", generate_review, name="generate_review"),
    path("user-histories/<int:user_id>", get_histories, name="get_histories"),
    path("histories/<int:history_id>", get_history, name="get_history"),
    path("solution/<int:problem_id>", solution_view, name="solution_view"),
    path("history/<int:history_id>", handle_history, name="handle_history"),
    path("problem/<int:problem_id>", handle_problem, name="handle_problem"),
    path("histories/<int:problem_id>/first-review", get_first_review, name="get_first_review")
]