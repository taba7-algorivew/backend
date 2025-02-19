from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from .models import History, Review, Problem, Solution
from user_auth.models import AlgoReviewUser
from .ai_module import generate_ai_review, generate_chatbot, generate_solution_code  # ai_module에서 함수 불러오기
from .input_source_precessing import get_the_url, get_info_img
from django.shortcuts import get_object_or_404

#[GET] /api/v1/api : 디버깅용 주소
@api_view(["GET"])
def hello_algoreview(request):
    return Response({"message": "Hello, Algo-Reviews!!!"}, status=status.HTTP_200_OK)

#[GET] /api/v1/user-histories/{user_id}
@api_view(["GET"])
def get_histories(request, user_id):
    histories = History.objects.filter(user_id=user_id, is_deleted=False) \
        .select_related("problem_id") \
        .values("id", "problem_id", "problem_id__name", "name") \
        .order_by("-created_at")

    # 조회된 히스토리가 없을 경우 즉시 반환
    if not histories.exists():
        print(f"No history found for user_id: {user_id}")
        return Response({"problems": []}, status=status.HTTP_200_OK)

    # 같은 문제 번호를 가진 데이터들을 뭉쳐두기
    problem_set = set()
    problem_dict = {}
    problems = []

    for history in histories:
        problem_id = history["problem_id"]
        problem_name = history["problem_id__name"]
        name = history["name"]
        history_id = history["id"]

        if problem_id in problem_set:
            problem_row = problem_dict[problem_id]
            problem_row['history_names'].append(name)
            problem_row['history_ids'].append(history_id)
        else:
            problem_dict[problem_id] = {
                "problem_id": problem_id,
                "problem_name": problem_name,
                "history_names": [name],
                "history_ids": [history_id],
            }
            problems.append(problem_dict[problem_id])
            problem_set.add(problem_id)

    return Response({"problems": problems}, status=status.HTTP_200_OK)

#[GET] /api/v1/histories/{history_id}
@api_view(['GET'])
def get_history(request, history_id) :
    history= History.objects.filter(id=history_id).first()
    problem= Problem.objects.filter(id= history.problem_id.id).first()
    reviews= Review.objects.filter(history_id=history_id).values("id", "title", "content", "start_line_number", "end_line_number", "is_passed")
    for review in reviews :
        review["comments"]= review["content"]
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

#[POST] /api/v1/review
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
    
    if problem is not None:
        prob = f"{problem.title}\n{problem.content}"
    else:
        raise AssertionError

    #############################################################
    #                        코드 리뷰 생성                      #
    #############################################################
    reviews = data.get("reviews", [])
    final_list = generate_ai_review(prob, source_code, reviews)

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

    for review in final_list:
        title= review[0]
        comments= review[1]
        start_line_number= review[2]
        end_line_number = review[3]
        is_passed = review[4]
        review_row= Review.objects.create(
            history_id= history,
            title= title,
            content= comments,
            start_line_number= start_line_number,
            end_line_number= end_line_number,
            is_passed = is_passed
        )
        review_data = {
            #"review_id": review_row.id,
            "id": review_row.id,
            "title": review[0],
            "comments": review[1],
            "start_line_number": review[2],
            "end_line_number": review[3],
            "is_passed": review[4]
        }
        return_data["reviews"].append(review_data)

        # 히스토리 이름 지정
        history.name= return_data["reviews"][0]["title"] #리뷰의 첫번째 타이틀
        history.save()
        return_data["history_name"]= history.name

    return Response(return_data, status=status.HTTP_201_CREATED)

# [PUT], [DELETE] /api/v1/history/{history_id}
@api_view(["PUT", "DELETE"])
def handle_history(request, history_id) :
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
    
# [PUT], [DELETE] /api/v1/problem/{problem_id}
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
    
# [GET, POST] /api/v1/solution/{problem_id}
@api_view(["GET", "POST"])
def solution_view(request, problem_id):
    # 문제 존재 여부 검증 (존재하지 않으면 404 반환)
    problem = get_object_or_404(Problem, id=problem_id)

    if request.method == "GET":
        # 해당 problem_id에 대한 Solution 조회
        solution = Solution.objects.filter(problem_id=problem_id).first()

        if solution:
            is_created = True
            solution_code = solution.solution_code
        else:
            is_created = False
            solution_code = ""

        # 응답 데이터 구성
        return_data = {
            "is_created": is_created,
            "solution_code": solution_code
        }

        return Response(return_data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        # 요청 데이터에서 필드 추출
        problem_info = request.data.get("problem_info")
        source_code = request.data.get("source_code")
        reviews = request.data.get("reviews", [])

        # 기존에 생성된 Solution이 있는지 확인
        existing_solution = Solution.objects.filter(problem_id=problem_id).first()
        if existing_solution:
            return Response({
                "detail": "모범 답안이 이미 생성되었습니다.",
                "solution_code": existing_solution.solution_code
            }, status=status.HTTP_400_BAD_REQUEST)

        # AI 모듈을 사용하여 Solution 코드 생성
        solution_code = generate_solution_code(problem_info, source_code, reviews)

        # Solution 모델에 저장
        Solution.objects.create(
            problem_id=problem,
            solution_code=solution_code
        )

        # POST 요청 시 solution_code만 반환
        return Response({
            "solution_code": solution_code
        }, status=status.HTTP_201_CREATED)

# [POST] /api/v1/chatbot
@api_view(["POST"])
def chatbot(request) :
    try:
        data = request.data
        answer = generate_chatbot(data)  # 챗봇 응답 생성
        return Response({"response": answer}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Internal Server Error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
