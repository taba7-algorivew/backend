from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from review.views import get_histories

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data['user'] = {
            'email': self.user.email,
            'password': self.user.password
        }
        return response

@api_view(['POST'])
def register(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    username= email.split("@")[0]
    user = User.objects.create_user(username=username, email=email, password=password)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    username= email.split("@")[0]
    password = request.data.get('password')

    # 이메일과 비밀번호를 사용하여 사용자 인증
    user= authenticate(username=username, password=password)
    #user = get_user_model().objects.get(email=email)
    print(user, email, password)
    if user is not None:  # 인증이 성공했을 때
      dataList= get_histories(user.id)
      return Response({
        "message": "login success",
        "user_id" : user.id,
        "histories" : dataList,
      }, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Login Failed"}, status=status.HTTP_400_BAD_REQUEST)