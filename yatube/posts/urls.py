from django.urls import path

from . import views


app_name = 'posts'
urlpatterns = [
    path('', views.index, name='index'),
    path('group/<slug>/', views.group_posts, name="group_list"),
    # Профайл пользователя
    path('profile/<username>/', views.profile, name='profile'),
    # Просмотр записи
    path('posts/<post_id>/', views.post_detail, name='post_detail'),
    # Создание поста
    path('create/', views.post_create, name='post_create'),
    # Редактирование записей
    path('posts/<post_id>/edit/', views.post_edit, name='post_edit'),
]
