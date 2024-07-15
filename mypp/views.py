from django.shortcuts import render
from rest_framework import viewsets,filters,permissions,status
from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser,BasePermission
from rest_framework.authentication import TokenAuthentication
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action,api_view, permission_classes, parser_classes
from django.contrib.admin.views.decorators import staff_member_required
from .serializers import OrderSerializer
from .models import Order
# for sending email
from django.core.mail import EmailMultiAlternatives,send_mail
from django.template.loader import render_to_string
from django.shortcuts import redirect

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if request.method == 'GET':
        mangoes = Mango.objects.all()
        orders = Order.objects.all()
        mango_serializer = MangoSerializer(mangoes, many=True)
        order_serializer = OrderSerializer(orders, many=True)
        return Response({
            'mangoes': mango_serializer.data,
            'orders': order_serializer.data
        })

    elif request.method == 'POST':
        if 'add_mango' in request.data:
            mango_serializer = MangoSerializer(data=request.data)
            if mango_serializer.is_valid():
                mango_serializer.save()
                return Response(mango_serializer.data, status=status.HTTP_201_CREATED)
            return Response(mango_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'change_status' in request.data:
            order_id = request.data.get('order_id')
            try:
                order = Order.objects.get(id=order_id)
                order.status = 'Completed'
                order.save()
                send_mail(
                    'Order Completed',
                    f'Your order of {order.quantity} {order.mango.name}(s) has been completed.',
                    'ihanik.ad@gmail.com',
                    [order.user.email],
                    fail_silently=False,
                )
                return Response({'status': 'Order status updated'}, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

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
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
class IsUserId3(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.id == 3

class AdminMangoView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsUserId3]

    def post(self, request):
        print(request.user)  # Log the authenticated admin user
        serializer = MangoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)  # Log the authenticated user
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        print(request.user)  # Log the authenticated user
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class AdminOrderView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsUserId3]
    def get(self, request):
        print(request.user)  # Log the authenticated admin user
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        print(request.user)  # Log the authenticated admin user
        order_id = request.data.get('id')
        new_status = request.data.get('status')

        if new_status not in ['Pending', 'Completed']:
            return Response({'error': 'Invalid status. Allowed statuses are "Pending" or "Completed".'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            return Response({'status': 'Order status updated successfully.'}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
            
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
        serializer = serializers.UserLoginSerializer(data = self.request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username= username, password=password)
            
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                print(token)
                print(_)
                login(request, user)
                return Response({'token' : token.key, 'user_id' : user.id})
            else:
                return Response({'error' : "Invalid Credential"})
        return Response(serializer.errors)

class UserLogoutView(APIView):
    def get(self, request):
        request.user.auth_token.delete()
        logout(request)
        return redirect('login')
