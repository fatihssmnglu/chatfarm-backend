from django.urls import path
from .views import chat_api, chat_page

urlpatterns = [
    path("chat/", chat_api, name="chat_api"),
    path("chat-ui/", chat_page, name="chat_page"),
]