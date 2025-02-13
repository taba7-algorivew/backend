from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime

# Create your models here.
class Problem(models.Model) :
    name= models.CharField(max_length=20)
    title= models.TextField()
    content= models.TextField()
    
class History(models.Model) :
    user_id= models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    problem_id= models.ForeignKey(Problem, on_delete=models.CASCADE)
    name= models.CharField(max_length=25)
    type= models.SmallIntegerField()
    source_code= models.TextField()
    created_at= models.DateTimeField(default=datetime.now())
    is_deleted= models.BooleanField(default=False)

class Review(models.Model) :
    history_id= models.ForeignKey(History, on_delete=models.CASCADE)
    title= models.CharField(max_length=50)
    content= models.TextField()
    start_line= models.SmallIntegerField()
    end_line= models.SmallIntegerField()

class Solution(models.Model) :
    history_id= models.ForeignKey(History, on_delete=models.CASCADE)
    solution_code= models.TextField()