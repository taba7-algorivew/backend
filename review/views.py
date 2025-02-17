from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from .models import History, Review, Problem, Solution
from user_auth.models import AlgoReviewUser
from .ai_module import generate_ai_review  # ai_module에서 함수 불러오기

from .input_source_precessing import get_the_url, get_info_img
from .my_bot import client

# Create your views here.

@api_view(["GET"])
def get_histories(request, user_id) :
    print("유저 아이디로 조회 들어옴")
    # 유저의 삭제되지 않은 히스토리들 조회
    histories = History.objects.filter(user_id=user_id, is_deleted=False) \
        .select_related("problem_id") \
        .values("id", "problem_id", "problem_id__name", "name") \
        .order_by("-created_at")

    # 같은 문제 번호를 가진 데이터들을 뭉쳐두기
    problem_set= set() # 이미 뭉쳐진 번호가 있는지 체크하기 위함
    problem_dict= {} # 같은 문제 번호를 가진 히스토리를 뭉칠 곳
    problems= [] # 최종적으로 리턴할 데이터
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
    #print({"problems": problems})
    return Response(
        {"problems": problems}, 
        status=status.HTTP_200_OK,
        )       
    

@api_view(['GET'])
def get_history(request, history_id) :
    print("히스토리 아이디로 조회들어옴")
    history= History.objects.filter(id=history_id).first()
    problem= Problem.objects.filter(id= history.problem_id.id).first()
    reviews= Review.objects.filter(history_id=history_id).values("id", "title", "comments", "start_line_number", "end_line_num")
    return_data= {
        "problem_id": problem.id,
        "problem_info": problem.content,
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
    problem_id= data["problem_id"]
    problem_info = data["problem_info"]
    input_source= data["input_source"]
    input_data= data["input_data"]
    #user_id= int(data["user_id"]["userId"])
    user_id= int(data["user_id"])
    user= AlgoReviewUser.objects.get(id= user_id)
    source_code= data["source_code"]
    
    #############################################################
    #                       URL 또는 이미지                      #
    #                         데이터 처리                        #
    #############################################################
    problem= None
    # 문제에 대한 정보가 없는 경우에만 문제에 대한 정보 파악
    if not problem_id :
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
                content= problem_data["content"]
            )
            
    else :
        problem= Problem.objects.filter(id= problem_id).first()
    
    if problem_data["status"]:
        prob = f"{problem_data['title']}\n{problem_data['description']}"
    else:
        raise AssertionError
    # code = source_code
    
    #########################################################
    final_list = generate_ai_review(prob, source_code,problem_info)
    #########################################################

    # reviews= get_review(**params)
    # 히스토리 생성
    history= History.objects.create(
        user_id= user,
        problem_id= problem,
        name= "name",
        type= 1, # api를 통해 파악해야 할 컬럼
        source_code= source_code,
    )

    # "problem_info" : prob
    return_data = {
        "history_id": history.id,
        "history_name": None, # 리뷰 정제 후 지정
        "problem_id": problem.id,
        "problem_info": problem.content,
        "reviews": []
    }

    #print(final_list)
    for review in final_list:
        title= review[0]
        comments= review[1]
        start_line_number= review[2]
        end_line_number = review[3]
        review_row= Review.objects.create(
            history_id= history,
            title= title,
            content= comments,
            start_line_number= start_line_number,
            end_line_number= end_line_number
        )
        review_data = {
            "review_id": review_row.id,
            "title": review[0],
            "comments": review[1],
            "start_line_number": review[2],
            "end_line_number": review[3]
        }
        return_data["reviews"].append(review_data)
        # 히스토리 이름 지정
        history.name= return_data["reviews"][0]["title"] #리뷰의 첫번째 타이틀
        history.save()
        return_data["history_name"]= history.name
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
        return Response(status=status.HTTP_200_OK,)

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
    
    if request.method == "PUT" :
        new_name= request.data.get("new_name")
        problem.name= new_name
        problem.save()
        return Response(status=status.HTTP_200_OK)
    
    elif request.method == "DELETE" :
        history= History.objects.filter(problem_id=problem).update(is_deleted=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
    else :
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
# 모범 답안 조회
@api_view(["GET"])
def get_solution(request, history_id) :
    solution= Solution.objects.filter(history_id=history_id).first()
    return_data= {
        "history_id": history_id,
        "solution_code": solution.solution_code
    }
    return Response(return_data, status=status.HTTP_200_OK)

# chatbot api
@api_view(["POST"])
def chatbot(request) :
    data= request.data
    answer= data["question"][-1]
    # 임의의 대답을 생성하기 위한 가짜 코드
    from random import random
    rand_num= random()
    if rand_num < 0.333333333333 :
        answer= f"'{answer}' 라는 질문은.. 저도 궁금해요.."
    elif rand_num < 0.66666666666666666 :
        answer= f"혹시 제게 '{answer}' 라고 물어보셨나요?"
    else :
        answer= f"안들린다아아아 안들린다아아아 {answer} 안들린다아아아아"
    return_data= {"response": answer}
    return Response(return_data, status=status.HTTP_200_OK)