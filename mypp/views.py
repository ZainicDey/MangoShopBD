from django.shortcuts import render
from rest_framework import viewsets,filters,permissions
from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authentication import TokenAuthentication
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.contrib.admin.views.decorators import staff_member_required
# for sending email
from django.core.mail import EmailMultiAlternatives,send_mail
from django.template.loader import render_to_string
from django.shortcuts import redirect

@staff_member_required
def admin_dashboard(request):
    mangoes = models.Mango.objects.all()
    orders = models.Order.objects.all()

    if request.method == 'POST':
        if 'add_mango' in request.POST:
            serializer = serializers.MangoSerializer(data=request.POST, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return redirect('admin_dashboard')
        elif 'change_status' in request.POST:
            order_id = request.POST.get('order_id')
            order = models.Order.objects.get(id=order_id)
            order.status = 'Completed'
            order.save()
            send_mail(
                'Order Completed',
                f'Your order of {order.quantity} {order.mango.name}(s) has been completed.',
                'ihanik.ad@gmail.com',
                [order.user.email],
                fail_silently=False,
            )
            return redirect('admin_dashboard')

    mango_serializer = serializers.MangoSerializer()
    order_serializer = serializers.OrderSerializer()

    context = {
        'mangoes': mangoes,
        'orders': orders,
        'mango_serializer': mango_serializer,
        'order_serializer': order_serializer,
    }
    return render(request, 'admin_dashboard.html', context)

class SellerViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = serializers.Seller.objects.all()
    serializer_class = serializers.SellerSerializer

class MangoViewSet(viewsets.ModelViewSet):
    queryset = models.Mango.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializers.MangoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.OrderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Order.objects.all()
        return models.Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_orders(self, request):
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def change_status(self, request, pk=None):
        order = self.get_object()
        order.status = 'Completed'
        order.save()
        send_mail(
            'Order Completed',
            f'Your order of {order.quantity} {order.mango.name}(s) has been completed.',
            'ihanik.ad@gmail.com',
            [order.user.email],
            fail_silently=False,
        )
        return Response({'status': 'Order status updated'})
        
class UserRegistrationApiView(APIView):
    serializer_class = serializers.RegistrationSerializer  
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            print(user)
            token = default_token_generator.make_token(user)
            print("token ", token)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            print("uid ", uid)
            confirm_link = f"https://mangoshopbd.onrender.com/active/{uid}/{token}"
            email_subject = "Confirm Your Email"
            email_body = render_to_string('confirm_email.html', {'confirm_link' : confirm_link})
            
            email = EmailMultiAlternatives(email_subject , '', to=[user.email])
            email.attach_alternative(email_body, "text/html")
            email.send()
            return Response("Check your mail for confirmation")
        return Response(serializer.errors)


def activate(request, uid64, token):
    try:
        uid = urlsafe_base64_decode(uid64).decode()
        user = User._default_manager.get(pk=uid)
    except(User.DoesNotExist):
        user = None 
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return redirect('register')
    

class UserLoginApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = serializers.UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)
            
            if user:
                login(request, user)  # Log in the user
                token, _ = Token.objects.get_or_create(user=user)
                return Response({'token': token.key, 'user_id': user.id})
            else:
                return Response({'error': "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # Delete the token
        logout(request)  # Log out the user
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
