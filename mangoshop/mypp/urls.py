from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SellerViewSet, MangoViewSet, OrderViewSet
from . import views
#media url
from django.conf.urls.static import static
from django.conf import settings
router = DefaultRouter()
router.register(r'sellers', SellerViewSet)
router.register(r'mangoes', MangoViewSet)
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.UserRegistrationApiView.as_view(), name='register'),
    path('login/', views.UserLoginApiView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('active/<uid64>/<token>/', views.activate, name = 'activate'),
    path('orders/my_orders/', OrderViewSet.as_view({'get': 'my_orders'}), name='my-orders'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
