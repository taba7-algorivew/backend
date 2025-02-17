from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from .models import History, Review, Problem
from user_auth.models import AlgoReviewUser
from .ai_module import generate_ai_review  # ai_module에서 함수 불러오기

from .input_source_precessing import get_the_url, get_info_img
from .my_bot import client

# Create your views here.

@api_view(["GET"])
def get_histories(request, user_id) :
    # 히스토리 불러오는 코드 부분, review app에 분리해야할 부분으로 생각되어짐, 일단 구현
    histories = History.objects.filter(user_id=user_id) \
        .select_related("problem_id") \
        .values("id", "problem_id", "problem_id__name", "name") \
        .order_by("-created_at")


    problem_set= set()
    problem_dict= {}
    problems= []
    for history in histories :
        # 문제 정보
        problem_id= history["problem_id"]
        problem_id__name= history["problem_id__name"]
        # 히스토리 정보
        name= history["name"]
        history_id= history["id"]
        # 이 주석 아래 부분에 problem_id__name부분을 problem_id로 수정하기
        # 문제 정보 같은 게 있는지 확인
        if problem_id in problem_set :
            problem_row= problem_dict[problem_id]
            problem_row['history_names'].append(name)
            problem_row['history_ids'].append(history_id)
        else :
            problem_dict[problem_id]= {
                "problem_id": problem_id,
                "problem_name": problem_id__name,
                "history_names": [name],
                "history_ids": [history_id],
            }
            
            problems.append(problem_dict[problem_id])
    print({"problems": problems})
    return Response(
        {"problems": problems}, 
        status=status.HTTP_200_OK,
        )       
    

@api_view(['GET'])
def get_history(request, history_id) :
    history= History.objects.filter(id=history_id).first()
    reviews= Review.objects.filter(history_id=history_id).values("id", "title", "comments", "start_line_number", "end_line_num")
    return_data= {
        "problem_info": history.problem_id,
        "source_code": history.source_code,
        "history_id": history.id,
        "reviews": reviews,
    }
    return Response(
        return_data,
        status=status.HTTP_200_OK,
    )
            
            
            
  
@api_view(["POST"])
def generate_review(request):
    # POST 데이터 처리
    data= request.data
    problem_info = data["problem_info"]
    problem= None
    input_source= data["input_source"]
    input_data= data["input_data"]
    user_id= int(data["user_id"]["userId"])
    user= AlgoReviewUser.objects.get(id= user_id)
    source_code= data["source_code"]
    
    #############################################################
    #                       URL 또는 이미지                      #
    #                         데이터 처리                        #
    #############################################################
    # 문제에 대한 정보가 없는 경우에만 문제에 대한 정보 파악
    if not problem_info :
        print("success?")
        # URL에 대한 처리
        if input_source == "url" :
            problem_data= get_the_url(input_data)
        # 이미지에 대한 처리
        else :
            problem_data= get_info_img(input_data)
        # 처리 결과 다루기
        if problem_data["status"] == True :
            # 문제 생성, 이 부분은 수정해야할 수 있습니다. 리뷰 생성 실패 시 데이터 삭제를 고려해야할 수 있습니다.
            name= problem_data["title"][:20]
            problem= Problem.objects.create(
                name= name,
                title= problem_data["title"],
                content= problem_data["description"]
            )
            
    else :
        problem= Problem.objects.filter(id= problem_info)
    
    # 히스토리 이름 기본값 생성
    now= datetime.now()
    default_name= now.strftime("%Y-%m-%d: %H:%M:%S")
    
    
    # 문제 정보와 소스코드로 API에게 리뷰 생성 요청



    if problem_data["status"]:
        prob = f"{problem_data['title']}\n{problem_data['description']}"
    else:
        raise AssertionError
    
    # "reviews" 리스트만 추출
    reviews = data.get("reviews", [])
    #########################################################
    final_list = generate_ai_review(prob, source_code, reviews)
    #########################################################

    # reviews= get_review(**params)
    # 히스토리 생성
    history= History.objects.create(
        user_id= user,
        problem_id= problem,
        name= default_name,
        type= 1, # api를 통해 파악해야 할 컬럼
        source_code= source_code,
    )

    # "problem_info" : prob
    return_data = {
        "history_id": history.id,
        "problem_info": problem.id,
        "reviews": []
    }

    # review_id는 1부터 시작하여 1씩 증가
    print(final_list)
    for review in final_list:
        title= review[0]
        comments= review[1]
        start_line_number= review[2]
        end_line_number = review[3]
        review_row= Review.objects.create(
            history_id= history,
            title= title,
            content= comments,
            start_line= start_line_number,
            end_line= end_line_number
        )
        review_data = {
            "review_id": review_row.id,
            "title": review[0],
            "comments": review[1],
            "start_line_number": review[2],
            "end_line_number": review[3]
        }
        return_data["reviews"].append(review_data)
    
    return Response(
        return_data, 
        status=status.HTTP_201_CREATED
        )

# 히스토리 불러오기("GET"), 히스토리 이름 바꾸기("PUT"), 히스토리 삭제("DELETE")
@api_view(["PUT", "DELETE"])
def handle_history(request, history_id) :
    # history_id로 객체 불러오기
    history= History.objects.filter(id= history_id).first()    
    if request.method == "PUT" :
        new_name= request.data.get("new_name")
        history= History.objects.get(id=history_id)
        history.name= new_name
        history.save()
        return Response({"name": new_name}, status=status.HTTP_200_OK,)

    elif request.method == "DELETE" :
        history.is_deleted= True
        history.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else :
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
# problem에 대한 이름 수정 또는 삭제
@api_view(["PUT", "DELETE"])
def handle_problem(request, problem_id):
    problem= Problem.objects.filter(id= problem_id).first()