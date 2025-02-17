from datetime import datetime
import re
import openai
import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

client = openai.Client(api_key=OPENAI_API_KEY)

##############system_prompt##################
def review_system_prompt() :
    feedback_content = [
        "<문제 설명> 은 알고리즘 문제에 대한 정보입니다.",
        "<풀이 코드> 는 <문제 설명>을 보고 유저가 작성한 프로그래밍 코드입니다.",
        "당신은 <풀이 코드>를 보고 <문제 설명>에 적합하고 잘 작동하는지를 보고 그에 맞는 피드백을 제공할 것.",
        "당신은 코드 리뷰를 제공하는 AI로서, 코드의 풀이(알고리즘) 설명과 성능 최적화 및 가독성 향상을 위한 코드에 대한 리뷰를 제공한다.",
        "당신은 <풀이 코드>가 <문제 설명>에 따라 잘 동작하는 경우, 성능 최적화 및 가독성 개선에 대한 피드백을 제시할 것.",
        "당신은 <풀이 코드>가 <문제 설명>에 따라 잘 동작하지 않는 경우, 그 원인을 분석하여 명확한 피드백을 제공할 것.",
        "<풀이 코드>가 <문제 설명>에 따라 잘 동작하지 않는 경우, Title과 피드백 제목을 작성할 때 알고리즘 개념 및 자료구조적인 내용을 포함할 것.",
        "예를 들어, 단순히 '오답 발생' 대신 'Two Pointers 조건 오류로 인한 부분합 계산 실패'처럼 코드와 밀접한 알고리즘 개념을 포함하여 표현할 것.",
        "입력 코드에서 수정 방안에 대한 방향성만 제시하며, 직접 코드 수정은 하지 않는다.",
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
    ]

    return feedback_content

def re_review_system_prompt() :
    correct_content = [
        "당신은 알고리즘 코드 리뷰를 제공하는 AI입니다.",
        "사용자가 제공한 코드(<풀이 코드>)가 주어진 문제(<문제 설명>)를 정확하게 해결하는지 평가하고, 최적화 및 가독성 개선을 위한 피드백을 제공합니다.",

        "## 리뷰 방식:",
        "1. **정확성 검토**",
        "   - <풀이 코드>가 <문제 설명>을 올바르게 해결하는지 확인합니다.",
        "   - 논리적 오류, 알고리즘의 적절성, 예외 처리 부족 여부 등을 분석합니다.",

        "2. **최적화**",
        "   - 코드의 성능을 향상시킬 수 있는 방법을 제안합니다.",
        "   - 시간 복잡도 및 공간 복잡도를 고려한 개선 방법을 설명합니다.",

        "3. **가독성 개선**",
        "   - 코드의 유지보수성을 높일 수 있도록 제안합니다.",
        "   - 변수명, 함수명, 주석, 코드 구조 등에 대한 개선점을 제공합니다.",

        "4. **기존 피드백 반영**",
        "   - <previous_feedback>을 참고하여, **기존 피드백이 해결된 경우 해당 피드백을 출력하지 않도록** 합니다.",
        "   - 해결된 피드백에 대해 '이 피드백은 해결되었습니다'라는 문구를 출력하지 말고, **출력 자체에서 제거해야 합니다.**",
        "   - 기존 피드백이 해결되었는지를 코드 변경 사항을 기반으로 자동으로 확인하고, 해결된 피드백은 최종 출력에서 **삭제**해야 합니다.",
        "   - 기존 피드백에서 해결되지 않은 부분이 있으면 이를 보완하고 새로운 피드백을 제시해야 합니다.",
        "   - **기존 피드백이 해결되었을 경우, 이를 새로운 피드백으로 변형하지 않고 리뷰에서 삭제해야 합니다.**",

        "## 출력 형식",
        "반드시 아래와 같은 형식으로 리뷰를 작성합니다.",
        "불필요한 추가 설명을 포함하지 말고, **명확한 제목과 논리적인 개선 방향**을 제공합니다.",

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

        "## 출력 형식 규칙",
        "- 각 피드백 제목에는 **핵심적인 알고리즘 개념 및 자료구조적인 내용을 포함**해야 합니다.",
        "- 단순히 **'오답 발생'** 같은 표현 대신, **'BFS 탐색 조건 오류로 인해 그래프 판별 실패'**처럼 구체적으로 작성합니다.",
        "- 기존 피드백(<previous_feedback>)을 먼저 반영한 후, **새로운 피드백을 추가**하여 정리합니다.",
        "- 기존 피드백이 해결되었을 경우, 해당 피드백은 최종 출력에서 **완전히 삭제해야 합니다.**",
        "- **불필요한 결론 요약 문구(예: '최종적으로,' '결론적으로,' '따라서' 등)를 생성하지 말고, 피드백 항목만 출력해야 합니다.**",
        "- **출력 맨 마지막에 '이전 피드백에서 제안된 내용이 이미 ~~' 같은 최종적인 요약을 하지 않도록 합니다.**",
        "- **피드백 항목 외에는 어떠한 문장도 출력하지 말고, 오직 피드백 목록만 유지해야 합니다.**",
        "- 해결된 피드백을 제거하고 새로운 피드백을 추가할 때, **출력 형식의 일관성을 유지**해야 합니다."
    ]
    return correct_content

def lines_system_prompt() :
    algorithm_content = [
        "유저가 제공한 코드에 대해 개선이 필요한 부분을 피드백한다.",
        "각 피드백에는 반드시 해당 코드의 시작 줄과 끝 줄을 포함해야 한다.",
        "피드백은 성능과 알고리즘 최적화 측면에서만 제공한다.",
        "각 피드백 항목은 반드시 다음 형식을 따라야 한다.",
        """
        피드백
        (시작 줄, 끝 줄) 가장 중요한 개선할 방향 및 이유

        예시:
        (5, 10) 반복문을 줄여서 시간 복잡도를 개선할 수 있음. 현재 O(n^2)이므로 O(n log n)으로 최적화 가능.
        """,
        "가장 중요한 개선 사항을 선택하여 제공해야 한다."
    ]
    return algorithm_content

def chatbot_system_prompt() -> list:
    """챗봇 시스템 프롬프트 반환"""
    return [
        {"role": "system", "content": "당신은 생성된 코드 리뷰 피드백 내용에 질문을 받는 AI입니다."},
        {"role": "system", "content": "< 문제 설명 >은 알고리즘 문제에 대한 정보입니다."},
        {"role": "system", "content": "< 풀이 코드 >은 알고리즘 풀이 코드에 대한 정보입니다."},
        {"role": "system", "content": "< 피드백 주제 >은 GPT 모델에게 받은 피드백 주제에 대한 정보입니다."},
        {"role": "system", "content": "< 피드백 내용 >은 피드백 주제에 대한 자세한 설명 정보입니다."},
        {"role": "system", "content": "< 질문 >은 현재 사용자가 요구하는 문의사항 입니다. 이를 잘 파악하여 상세한 답변을 해야 합니다."},
        {"role": "system", "content": "위 형식은 질문을 이해하기 위한 용도이며, 응답에서는 사용하지 않는다."},
        {"role": "system", "content": "답변에 마크다운 표기 및 모든 특수기호 서식을 사용하지 않는다. (예: **Bold**, _Italic_, `Code Block` 등) 오직 일반 텍스트로 답변하며, 줄바꿈은 표기한다."},
        {"role": "system", "content": "답변의 길이는 800 토큰으로 제한합니다."},
        {"role": "system", "content": "한국어로 답해야 합니다."},
        {"role": "system", "content": "교육적 어투로 답해야 합니다."}
    ]


########################chatgpt_function########################################

def chat_with_gpt(prompt, review_content):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": msg} for msg in review_content] + [
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    return response.choices[0].message.content


def chat2_with_gpt(prompt, line_content):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": msg} for msg in line_content] + [
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    return response.choices[0].message.content

#########################review, re_review function ############################################3

def generate_review(prob,source_code) :
    review_content = review_system_prompt()

    user_input = f"<문제 설명> {prob}\n<풀이 코드> {source_code}"

    content_response = chat_with_gpt(user_input, review_content)

    matches = re.findall(r'(\d+)\.\s*(.+?)\s*-\s*(.+?)(?=\n\d+\.|\Z)', content_response, re.DOTALL)
    result = [[title.strip(), content.strip()] for _, title, content in matches]

    return result

# "reviews"에서 [title,content]로 이루어진 리스트 previous_feedback
def generate_re_review(prob,source_code,reviews) :


    previous_list = [(review["title"], review["comments"]) for review in reviews]
    previous_feedback = f'"""\n{json.dumps(previous_list, indent=4, ensure_ascii=False)}\n"""'

    re_review_content = re_review_system_prompt()

    user_input2 = f"<문제 설명> {prob}\n<풀이 코드> {source_code}\n<previous_feedback>{previous_feedback}"

    re_content_response = chat_with_gpt(user_input2,re_review_content)

    matches = re.findall(r'(\d+)\.\s*(.+?)\s*-\s*(.+?)(?=\n\d+\.|\Z)', re_content_response, re.DOTALL)
    result = [[title.strip(), content.strip()] for _, title, content in matches]

    return result
# final_list = generate_ai_review(prob, source_code,problem_info)

#########################Main Function###################################################
def generate_ai_review(prob : str, source_code : str, reviews : list) : 
    
    if reviews :
        result = generate_review(prob,source_code)
    else :

        generate_re_review(prob,source_code,reviews)     
    
    maybe_feedback = []
    line_content = lines_system_prompt()
    
    for title, content in result:
        user_input3 = f"피드백 제목 {title}\n피드백 내용 {content}\n문제 {prob}\n코드 {source_code}"
        response = chat2_with_gpt(user_input3, line_content)
        maybe_feedback.append(response)

    final_list = []
    for (title, feedback) in zip([t.strip("*") for t, _ in result], maybe_feedback):
        match = re.search(r"\((\d+),\s*(\d+)\)\s*(.*)", feedback, re.DOTALL)
        if match:
            start_line, end_line, content = match.groups()
            final_list.append([title, content.strip(), int(start_line), int(end_line)])
    

    return final_list

def generate_chatbot(request_data: dict) -> str:
    messages = chatbot_system_prompt()    # 프롬프트 불러오기

    # 기존 대화 이력 추가
    for q, r in zip(request_data["questions"], request_data["answers"]):
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": r})

    # 새 질문 추가
    messages.append({
        "role": "user",
        "content": (
            f"< 문제 설명 >\n{request_data['problem_info']}\n\n"
            f"< 풀이 코드 >\n{request_data['source_code']}\n\n"
            f"< 피드백 주제 >\n{request_data['review_info']['title']}\n\n"
            f"< 피드백 내용 >\n{request_data['review_info']['comments']}\n\n"
            f"< 질문 >\n{request_data['questions'][-1]}\n\n"
            "이 내용을 바탕으로 상세한 답변을 생성하세요."
        )
    })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=800
        )
        return response.choices[0].message["content"]
    except openai.OpenAIError as e:
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        return f"Internal Server Error: {str(e)}"

### 모범답안
'''
def code_system_prompt () :
    final_content = [
        "당신은 코드 개선을 전문으로 하는 AI 엔지니어입니다.",
        "사용자가 제공한 코드(<code>)는 <prob>을 해결하기 위해 작성된 풀이 코드입니다.",
        "사용자는 FINAL_LIST에 포함된 피드백을 바탕으로 <code>를 개선하여 최적의 성능과 가독성을 갖춘 최종 모범 코드(Final Code)를 원합니다.",

        "## 입력 데이터 설명",
        "1. <문제 설명> : 유저가 해결해야 할 문제의 설명입니다.",
        "2. <풀이 코드> : 유저가 문제를 해결하기 위해 작성한 코드입니다.",
        """3. <FINAL_LIST> :
        - 형식: `[피드백 제목, 피드백 내용, 시작 줄 번호, 끝 줄 번호]`",
        - 이 리스트는 코드에서 개선이 필요한 부분과 수정 방향을 제공합니다.",
        - 각 피드백 항목은 특정 코드 영역(시작 줄 ~ 끝 줄)에 해당하므로, 해당 코드 영역을 수정해야 합니다.""",

        """## 코드 개선 방식
        1. **FINAL_LIST에 제공된 피드백을 기반으로 필요한 부분만 수정**,
        - 피드백이 적용되는 줄 번호(시작 줄 ~ 끝 줄)를 기준으로 해당 부분을 변경합니다.,
        - 피드백을 반영하되, **기존 코드의 구조와 논리는 유지**합니다.""",

        """2. **코드의 가독성과 성능을 최적화**
        - 불필요한 반복문 제거, 알고리즘 최적화, 변수명 개선 등을 수행합니다.,
        - 코드의 유지보수성을 높이기 위해 주석을 추가할 수 있습니다.""",

        """3. **불필요한 변경을 하지 않음**,
        - 피드백에 언급되지 않은 코드 부분은 변경하지 않습니다.,
        - 코드의 스타일과 논리를 유지하면서, 오직 필요한 부분만 수정합니다.""",

        """## 출력 형식
        최종적으로 개선된 코드(Final Code)만 출력해야 합니다.,
        Final Code는 사용자의 기존 코드(code)에서 필요한 부분만 변경한 최적의 버전이어야 합니다.,
        불필요한 설명이나 추가 주석 없이, 수정된 코드만 출력합니다."""
    ]

    return final_content

def chat3_with_gpt(prompt):
    response = response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
   *[{"role": "system", "content": msg} for msg in final_content],
        {
        "role": "user",
        "content": prompt
        }
    ],
        max_tokens=1000,
        temperature=0.7,
    )

    return response.choices[0].message.content


# 테스트 실행
def generate_final_code(final_list,source_code,prob) :
    final_feedback = f'"""{json.dumps(final_list)}"""'

    user_input3 = "<문제 설명>" + prob + "\n" + "<풀이 코드>" + source_code + "\n" + "<FINAL_LIST>" + final_feedback
    code_response = chat3_with_gpt(user_input3)
    ## string ##

    return code_response

'''
