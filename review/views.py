from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from .models import History, Review, Problem
from user_auth.models import AlgoReviewUser


from .input_source_precessing import get_the_url, get_info_img

# Create your views here.

def get_histories(user_id) :
    # 히스토리 불러오는 코드 부분, review app에 분리해야할 부분으로 생각되어짐, 일단 구현
    histories = History.objects.filter(user_id=user_id) \
        .select_related("problem_id") \
        .values("id", "problem_id", "problem_id__name", "name", "created_at") \
        .order_by("-created_at")


    print(histories)
    problem_dict_history_list= {}
    for history in histories :
    # 문제 아이디
        problem_name= history["problem_id__name"]
        if problem_name not in problem_dict_history_list :
            problem_dict_history_list[problem_name]= [history]
        else :
            problem_dict_history_list[problem_name].append(history)
              
    print(problem_dict_history_list)
    return problem_dict_history_list
  
@api_view(["POST"])
def generate_review(request):
    # POST 데이터 처리
    data= request.data
    print(data)
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
    # reviews= get_review(**params)
    # 히스토리 생성
    history= History.objects.create(
        user_id= user,
        problem_id= problem,
        name= default_name,
        type= 1, # api를 통해 파악해야 할 컬럼
        source_code= source_code,
    )
    return_data= {
        "history_id": history.id,
        "problem_info": problem.id,
        "reviews": [
            {
                "review_id": 1,
                "title": "캐시 교체 알고리즘 오류",
                "comments": "LRU 알고리즘을 올바르게 구현하려면, 가장 최근에 사용된 항목을 맨 뒤로 보내야 합니다.\n하지만 현재 코드에서는 기존 항목을 삭제하고 마지막에 추가하고 있습니다.",
                "start_line_number": 3,
                "end_line_number": 5
            },
            {
                "review_id": 2,
                "title": "대소문자 처리 누락",
                "comments": "도시 이름을 비교하기 전에 소문자로 변환해야 합니다.\n그러나 현재 코드에서는 소문자로 변환된 도시 이름으로 비교하고 있습니다.",
                "start_line_number": 8,
                "end_line_number": 10
            },
            {
                "review_id": 3,
                "title": "초기 캐시가 비어있는 경우 처리",
                "comments": "캐시가 비어있는 경우를 처리하지 않고 있습니다.\n초기 캐시가 비어있을 때의 조건을 추가하여 예외 사항을 고려하세요.",
                "start_line_number": 12,
                "end_line_number": 15
            }
  ]
    }
    return Response(
        return_data, 
        status=status.HTTP_201_CREATED
        )

# 히스토리 불러오기("GET"), 히스토리 이름 바꾸기("PUT"), 히스토리 삭제("DELETE")
@api_view(["GET", "PUT", "DELETE"])
def handle_history(request, history_id) :
    # history_id로 객체 불러오기
    history= History.objects.filter(id= history_id).first()
    if request.method == "GET":
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
    
    elif request.method == "PUT" :
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