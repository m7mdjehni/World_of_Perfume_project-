from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),

    # REST API (full CRUD)
    path('api/products/', views.PerfumeListCreateView.as_view(), name='product_list_api'),
    path('api/products/add/', views.PerfumeListCreateView.as_view(), name='add_product_api'),
    path('api/products/<int:pk>/', views.PerfumeDetailView.as_view(), name='product_detail_api'),

    # Orders (authenticated users only)
    path('api/orders/', views.OrderCreateView.as_view(), name='order_create_api'),

    # AI Integration
    path('api/products/generate-description/', views.generate_description_api, name='generate_description_api'),
]
