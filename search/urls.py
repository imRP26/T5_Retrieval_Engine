from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search', views.search, name='index'),
    path('imageSearch', views.imageSearch, name='imageSearch'),
    path('newsSearch', views.newsSearch, name='newsSearch')
]
