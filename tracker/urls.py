from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Adjust these names/paths to match your views.py
    path('', views.home, name="home"),
    path('diet-plan/', views.diet_plan, name="diet_plan"),
    path('register/', views.register, name='register'),
    path('setup/', views.profile_setup, name='profile_setup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-food/', views.add_food, name='add_food'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('logout/', views.logout_view, name='logout'),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path('update-weight/', views.update_weight, name='update_weight'),
    path('update-water/', views.update_water, name='update_water'),

]
