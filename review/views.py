from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from .models import History, Review, Problem
from user_auth.models import AlgoReviewUser


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
    # code = source_code

    # 이전 코드 리뷰
    # previous_feedback = []

    feedback_content = [
        "< 문제 설명 > 은 알고리즘 문제에 대한 정보입니다.",
        "<풀이 코드> 는 <문제 설명>을 보고 유저가 작성한 프로그래밍 코드입니다.",
        "당신은 <풀이 코드>를 보고 <문제 설명>에 적합하고 잘 작동하는지를 보고 그에 맞는 피드백을 제공할 것.",
        "당신은 코드 리뷰를 제공하는 AI로서, 코드의 풀이(알고리즘) 설명과 성능 최적화 및 가독성 향상을 위한 코드에 대한 리뷰를 제공한다.",
        "당신은 <풀이 코드>가 <문제 설명>에 따라 잘 동작하는 경우, 성능 최적화 및 가독성 개선에 대한 피드백을 제시할 것.",
        "당신은 <풀이 코드>가 <문제 설명>에 따라 잘 동작하지 않는 경우, 그 원인을 분석하여 명확한 피드백을 제공할 것.",
        "<풀이 코드>가 <문제 설명>에 따라 잘 동작하지 않는 경우, Title과 피드백 제목을 작성할 때 알고리즘 개념 및 자료구조적인 내용을 포함할 것.",
        "예를 들어, 단순히 '오답 발생' 대신 'Two Pointers 조건 오류로 인한 부분합 계산 실패'처럼 코드와 밀접한 알고리즘 개념을 포함하여 표현할 것.",
        "입력  코드에서 수정 방안에 대한 방향성만 제시하며, 직접 코드 수정은 하지 않는다.",
        "방향성에 대한 이유를 논리적인 근거로 명확하게 제시할 것.",
        "출력 형식은 반드시 다음을 따라야 한다.",
        """
        <Title> 피드백의 핵심 요약을 한 줄로 작성합니다.</Title>

        <Content>
        1. 피드백 제목
        - 피드백 내용 상세 설명

        2. 피드백 제목
        - 피드백 내용 상세 설명

        3. 피드백 제목
        - 피드백 내용 상세 설명
        </Content>
        """,
        "출력 형식에 불필요한 추가 설명을 포함하지 말 것.",
        "각 피드백 제목에서 '[ ]' 기호를 제거하여 자연스럽게 출력할 것.",
        "각 피드백 제목은 핵심적인 알고리즘 개념 및 코드 동작 방식과 관련이 있도록 구체적으로 작성해야 한다.",
        "피드백 제목을 일반적인 키워드가 아니라, 개선해야 할 코드 동작 및 알고리즘 개념을 포함한 형태로 작성해야 한다.",
        "피드백 내용에는 논리적인 개선 이유를 포함해야 한다.",
        "각 피드백 항목을 번호 순서대로 나열하여 정리할 것.",
        "반드시 모든 피드백과 제목은 한국어로 작성해야 한다.",
        "영어 단어나 문장은 피드백 내용에 포함하지 말 것.",
        "한국어로 자연스럽게 표현할 것. (예: 'Two Pointers' 대신 '투 포인터' 사용)",
    ]

    review_content = feedback_content

    def chat_with_gpt(prompt):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
            *[{"role": "system", "content": msg} for msg in review_content],
            {
                "role": "user",
                "content": prompt
            }
        ],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    
    user_input = "< 문제 설명 >" + prob + "\n" + "<풀이 코드>" + source_code
    content_response = chat_with_gpt(user_input)
    import re

    # 정규식을 사용하여 항목 추출
    print(f"{content_response=}")
    #matches = re.findall(r'\d+\.\s(.+?)\n\s+-\s(.+?)(?=\n\d+\.|\Z)', content_response, re.DOTALL)
    cleaned_content = re.sub(r'\s*\n\s*', '\n', content_response)  # 개행 전후 불필요한 공백 제거
    cleaned_content = re.sub(r'\n-\s*', '\n- ', cleaned_content)  # `-` 앞뒤 공백 정리

    matches = re.findall(r'\d+\.\s(.+?)\n-\s(.+?)(?=\n\d+\.|\Z)', cleaned_content, re.DOTALL)
    print(f"{matches=}")
    # 리스트 변환
    result = [[title.strip(), content.strip()] for title, content in matches]
    print(f"{result=}")
    # Content 부분 추출
    content_lines = content_response.split("\n")

    # 각 번호별 내용을 저장할 리스트
    title_list = []

    # 번호가 포함된 줄을 title_list에 추가하면서 "번호. " 제거
    for line in content_lines:
        line = line.strip()
        match = re.match(r"^\d+\.\s*(.*)", line)  # 숫자와 점(.) 이후 공백을 제외한 내용 추출
        if match:
            title_list.append(match.group(1))  # 정규식 그룹에서 내용만 추가

    algorithm_content = [
        "유저가 제공한 코드에 대해 개선이 필요한 부분을 피드백한다.",
        "각 피드백에는 반드시 해당 코드의 시작 줄과 끝 줄을 포함해야 한다. 시작 줄과 끝 줄을 명확히 제시하지 않은 피드백은 유효하지 않다.",
        "피드백은 가독성이 아닌 성능과 알고리즘 최적화 측면에서만 제공한다.",
        "코드를 직접 수정하지 않고, 개선 방향과 이유만 설명한다.",
        "코드를 직접 제공하지 않는다.",
        "각 피드백 항목은 반드시 다음 형식을 따라야 한다.",
        """
        피드백
        (시작 줄, 끝 줄) 가장 중요한 개선할 방향 및 이유

        예시:

        (5, 10) 반복문을 줄여서 시간 복잡도를 개선할 수 있음. 현재 O(n^2)이므로 O(n log n)으로 최적화 가능.
        """,
        "모든 피드백에는 시작 줄과 끝 줄이 반드시 포함되어야 하며, 가까운 줄이라도 정확한 줄 번호를 명시해야 한다.",
        "단 하나의 피드백만 제공해야 하며, 가장 중요한 개선 사항을 선택하여 제공해야 한다."
    ]



    # "gpt-3.5-turbo", "gpt-4o"
    def chat2_with_gpt(prompt):
        response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
    *[{"role": "system", "content": msg} for msg in algorithm_content],
            {
            "role": "user",
            "content": prompt
            }
        ],
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content
    
    ### 피드백제목,내용
    maybe_feedback = list()

    for i in range(len(result)) :
        user_input3 = "피드백 제목"+result[i][0] + "\n"+ "피드백 내용" + result[i][1] + "\n" + "문제" + prob + "\n" + "코드" + source_code
        response = chat2_with_gpt(user_input3)
        print(f"{response=}")
        maybe_feedback.append(response)



    cleaned_title_list = [title.strip("*") for title in title_list]
    # [피드백제목, 피드백 내용, 시작줄, 끝줄] 을 가지는 리스트를 만든다.

    # 최종 결과를 저장할 리스트
    final_list = []
    temp_list = []
    # 각 피드백을 순회하며 (시작 줄, 끝 줄), 내용 추출
    for title, feedback in zip(cleaned_title_list, maybe_feedback):
        match = re.search(r"\((\d+),\s*(\d+)\)\s*(.*)", feedback, re.DOTALL)  # (시작 줄, 끝 줄) 및 내용 추출
        if match:
            start_line, end_line, content = match.groups()
            temp_list.append([title, content.strip()])
            final_list.append([title, content.strip(), int(start_line), int(end_line)])



    # reviews= get_review(**params)
    # 히스토리 생성
    history= History.objects.create(
        user_id= user,
        problem_id= problem,
        name= default_name,
        type= 1, # api를 통해 파악해야 할 컬럼
        source_code= source_code,
    )

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

    print(return_data)
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