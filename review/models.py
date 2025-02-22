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
    name= models.CharField(max_length=255)
    type= models.SmallIntegerField()
    source_code= models.TextField()
    revision = models.PositiveIntegerField(default=1)
    created_at= models.DateTimeField(default=datetime.now)
    is_deleted= models.BooleanField(default=False)

class Review(models.Model) :
    history_id= models.ForeignKey(History, on_delete=models.CASCADE)
    title= models.CharField(max_length=255)
    content= models.TextField()
    start_line_number= models.SmallIntegerField()
    end_line_number= models.SmallIntegerField()
    is_passed= models.BooleanField(default=False) # 기본값은 통과하지 못했다는 뜻으로 False

class Solution(models.Model) :
    problem_id= models.ForeignKey(Problem, on_delete=models.CASCADE)
    solution_code= models.TextField()

class SolutionLine(models.Model):
    solution_id = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name="solution_lines")
    start_line_number = models.SmallIntegerField()
    end_line_number = models.SmallIntegerField()
