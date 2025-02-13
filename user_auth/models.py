from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# Create your models here.
class AlgoReviewUser(AbstractUser):
    # id는 gpt에 의하면, 알아서 생성되는 필드라고 한다.
    # id= models.AutoField(primary_key=True) 
    email= models.EmailField(unique=True)
    password= models.CharField()
    
    # 불필요한 컬럼 비활성화
    last_login= None
    first_name= None
    last_name=None
    date_joined= None
    
    groups = models.ManyToManyField(
        Group,
        related_name="algo_review_users",
        blank=True,
    )
    user_permissions= models.ManyToManyField(
        Permission,
        related_name="algo_review_users",
        blank=True,
    )
    
    def __str__(self) :
        return self.email