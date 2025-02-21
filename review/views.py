from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from .models import History, Review, Problem, Solution, SolutionLine
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

# [POST] /api/v1/review
@api_view(["POST"])
def generate_review(request):
    # POST 데이터 처리
    data = request.data
    problem_id = data.get("problem_id")
    problem_info = data.get("problem_info")
    user_id = int(data.get("user_id"))
    user = AlgoReviewUser.objects.get(id=user_id)
    source_code = data.get("source_code")

    #############################################################
    #                      URL 또는 이미지 처리                 #
    #############################################################
    problem = None
    if not problem_id:
        input_source = data.get("input_source")
        input_data = data.get("input_data")

        if input_source == "url":
            problem_data = get_the_url(input_data)
        else:
            problem_data = get_info_img(input_data)

        if problem_data.get("status"):
            name = problem_data["title"][:20]
            problem = Problem.objects.create(
                name=name,
                title=problem_data["title"],
                content=problem_data["content"]
            )
        else:
            return Response({"detail": "문제 정보를 가져오는 데 실패했습니다."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        problem = Problem.objects.filter(id=problem_id).first()

    if not problem:
        return Response({"detail": "해당 문제를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    prob = f"{problem.title}\n{problem.content}"

    #############################################################
    #                        코드 리뷰 생성                      #
    #############################################################
    reviews = data.get("reviews", [])
    final_list = generate_ai_review(prob, source_code, reviews)

    # 히스토리 생성
    history = History.objects.create(
        user_id=user,
        problem_id=problem,
        name="",  # 리뷰 생성 후 첫 번째 리뷰 타이틀로 업데이트 예정
        type=1,
        source_code=source_code,
    )

    return_data = {
        "history_id": history.id,
        "history_name": None,  # 리뷰 생성 후 지정
        "problem_id": problem.id,
        "problem_name": problem.name,
        "problem_info": problem.content,
        "reviews": []
    }

    for review in final_list:
        title, comments, start_line_number, end_line_number, is_passed = review

        review_row = Review.objects.create(
            history_id=history,
            title=title,
            content=comments,
            start_line_number=start_line_number,
            end_line_number=end_line_number,
            is_passed=is_passed
        )

        review_data = {
            "id": review_row.id,
            "title": title,
            "comments": comments,
            "start_line_number": start_line_number,
            "end_line_number": end_line_number,
            "is_passed": is_passed
        }
        return_data["reviews"].append(review_data)

    # 히스토리 이름 지정 (첫 번째 리뷰 타이틀 사용)
    if return_data["reviews"]:
        history.name = return_data["reviews"][0]["title"]
        history.save()
        return_data["history_name"] = history.name

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

            # SolutionLine 테이블에서 관련 라인 정보 추출 및 정렬
            lines = SolutionLine.objects.filter(solution_id=solution)
            lines_list = [
                {"start_line_number": line.start_line_number, "end_line_number": line.end_line_number}
                for line in lines
            ]
        else:
            is_created = False
            solution_code = ""
            lines_list = []

        # 응답 데이터 구성
        return_data = {
            "is_created": is_created,
            "solution_code": solution_code,
            "lines": lines_list
        }

        return Response(return_data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        # 요청 데이터에서 필드 추출
        problem_info = request.data.get("problem_info")
        source_code = request.data.get("source_code")
        reviews = request.data.get("reviews", [])

        # 기존에 생성된 Solution이 있는지 확인 (예외처리 제거 또는 간소화)
        if Solution.objects.filter(problem_id=problem_id).exists():
            return Response({"detail": "모범 답안이 이미 생성되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # AI 모듈을 사용하여 Solution 코드 및 라인 생성
        solution_code, lines = generate_solution_code(problem_info, source_code, reviews)

        # Solution 테이블에 저장
        solution = Solution.objects.create(
            problem_id=problem,
            solution_code=solution_code
        )

        # SolutionLine 테이블에 각 라인 정보 저장
        line_entries = [
            SolutionLine(
                solution_id=solution,
                start_line_number=start_line_number,
                end_line_number=end_line_number
            ) for _, start_line_number, end_line_number in lines
        ]
        SolutionLine.objects.bulk_create(line_entries)

        # 응답 데이터 구성
        response_data = {
            "solution_code": solution_code,
            "lines": [
                {"start_line_number": start_line_number, "end_line_number": end_line_number}
                for _, start_line_number, end_line_number in lines
            ]
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

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

# [GET] /api/v1/histories/{problem_id}/first-review
@api_view(["GET"])
def get_first_review(request, problem_id):
    """
    코드 리뷰의 최초 의뢰 기록 조회 API

    - problem_id로 history 테이블 필터링
    - created_at을 기준으로 오름차순 정렬하여 첫 번째 레코드의 history_id와 source_code 가져오기
    - 해당 history_id로 review 테이블에서 start_line_number, end_line_number 가져오기
    - 요청 성공 시 최초 코드 및 리뷰 라인 정보 반환

    응답 형식:
    {
        "first_code": "코드 문자열",
        "lines": [
            {"start_line_number": int, "end_line_number": int},
            ...
        ]
    }
    """
    # problem_id를 기반으로 history 레코드 조회
    first_history = (
        History.objects
        .filter(problem_id=problem_id, is_deleted=False)
        .order_by("created_at")
        .first()
    )

    if not first_history:
        return Response({"detail": "해당 문제의 히스토리를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 해당 history_id로 review 레코드 조회
    reviews = Review.objects.filter(history_id=first_history.id)

    # 리뷰 라인 정보 추출
    lines = [
        {"start_line_number": review.start_line_number, "end_line_number": review.end_line_number}
        for review in reviews
    ]

    response_data = {
        "first_code": first_history.source_code,
        "lines": lines
    }

    return Response(response_data, status=status.HTTP_200_OK)
