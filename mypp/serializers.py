from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Seller, Mango, Order

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class SellerSerializer(serializers.ModelSerializer):
    seller = UserSerializer()

    class Meta:
        model = Seller
        fields = ['id', 'seller']

class MangoSerializer(serializers.ModelSerializer):
    seller = SellerSerializer()

    class Meta:
        model = Mango
        fields = ['id', 'name', 'image', 'description', 'price', 'quantity', 'seller']

    def create(self, validated_data):
        seller_data = validated_data.pop('seller')
        seller, created = Seller.objects.get_or_create(**seller_data)
        mango = Mango.objects.create(seller=seller, **validated_data)
        return mango

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    mango = serializers.PrimaryKeyRelatedField(queryset=Mango.objects.all())

    class Meta:
        model = Order
        fields = ['id', 'user', 'mango', 'quantity', 'status', 'ordered_at']

    def create(self, validated_data):
        user = validated_data.pop('user')
        mango = validated_data.pop('mango')
        order = Order.objects.create(user=user, mango=mango, **validated_data)
        return order
    
class RegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(required = True)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'confirm_password']
    
    def save(self):
        username = self.validated_data['username']
        first_name = self.validated_data['first_name']
        last_name = self.validated_data['last_name']
        email = self.validated_data['email']
        password = self.validated_data['password']
        password2 = self.validated_data['confirm_password']
        
        if password != password2:
            raise serializers.ValidationError({'error' : "Password Doesn't Mactched"})
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'error' : "Email Already exists"})
        account = User(username = username, email=email, first_name = first_name, last_name = last_name)
        print(account)
        account.set_password(password)
        account.is_active = False
        account.save()
        return account
    
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required = True)
    password = serializers.CharField(required = True)
