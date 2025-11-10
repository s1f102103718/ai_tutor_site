from django.urls import path
from . import views, api

urlpatterns = [
    path('', views.chat_page, name='chat'),
    path('api/chat/', api.chat_with_ai, name='chat_api'),
    path('api/history/', api.get_history, name='get_history'),
    path("api/delete_history/", api.delete_chat_history, name="delete_chat_history"),
]
