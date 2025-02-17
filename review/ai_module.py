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
    "<문제 설명>은 알고리즘 문제에 대한 정보입니다.",
    "<풀이 코드>는 <문제 설명>을 보고 유저가 작성한 프로그래밍 코드입니다.",
    "당신은 <풀이 코드>를 보고 <문제 설명>에 적합하고 잘 작동하는지를 판단한 후, 정답에 가까워질 수 있도록 실질적인 개선 피드백을 제공해야 합니다.",
    
    "당신은 코드 리뷰를 제공하는 AI로서, <풀이 코드>의 **알고리즘적 접근 방식**, **논리적 오류**, **시간 복잡도 개선** 및 **정답률 향상**을 위한 피드백을 제공합니다.",
    
    "## ✅ 코드 리뷰 방식:",
    "1. **정확성 검토**",
    "   - <풀이 코드>가 <문제 설명>을 정확히 해결하는지 평가합니다.",
    "   - 논리적 오류, 조건 처리 오류, 엣지 케이스 미처리 등의 문제점을 분석합니다.",
    
    "2. **정답에 가까워질 수 있도록 개선 방향 제공**",
    "   - <풀이 코드>가 틀렸다면, **어떤 부분이 잘못되었는지 분석하고, 올바르게 수정할 방향을 한 문단으로 설명해야 합니다.**",
    "   - 단순히 '오답 발생'이라고 하지 말고, **어떤 개념이 부족한지, 어떤 논리적 오류가 있는지를 구체적으로 서술해야 합니다.**",
    
    "3. **최적화 필요 시 개선 방향 제공**",
    "   - 코드가 동작하지만 비효율적이라면, **시간 복잡도 및 공간 복잡도를 고려한 개선 방법을 한 문단으로 제안합니다.**",
    "   - 예를 들어, '현재 O(N^2) 복잡도를 가지므로 이진 탐색을 활용하면 O(log N)으로 개선 가능합니다.' 와 같이 작성해야 합니다.",
    
    "4. **가독성 피드백은 필요할 경우에만 제공**",
    "   - 코드가 **정확하지 않다면**, 가독성 피드백은 제공하지 않습니다. (정확성을 먼저 해결해야 함)",
    "   - 코드가 정확하게 동작하는 경우에만, 변수명 개선, 함수 구조 개선 등의 피드백을 한 문단으로 추가할 수 있습니다.",
    
    "5. **잘못된 피드백 제공 방지**",
    "   - 제목과 내용이 일치하지 않도록 발생하는 오류를 방지해야 합니다.",
    "   - **제목은 반드시 피드백 내용과 정확히 일치해야 합니다.**",
    "   - 이미 해결된 피드백이나 불필요한 피드백(예: '이 부분은 잘 작성되었습니다')은 출력하지 않습니다.",
    
    "6. **불필요한 마무리 문구 생성 금지**",
    "   - '이와 같은 개선을 통해 문제를 더 효율적으로 해결할 수 있습니다.' 같은 마무리 문장을 절대 출력하지 않습니다.",
    "   - '이 개선을 통해 코드는 더 효율적이며, 큰 입력에서도 성능을 유지할 수 있습니다.' 같은 마무리 문장을 절대 출력하지 않습니다.",
    "   - 피드백 내용 이후에 '따라서', '결론적으로', '이로 인해', '이러한 개선을 통해' 등의 문구를 포함한 마무리 문장을 절대 포함하지 않습니다.",
    "   - **오직 코드 리뷰 항목만 제공하며, 최종적으로 요약하거나 결론을 내리지 않습니다.**",
    
    "7. **하위 카테고리(-) 사용 금지**",
    "   - 코드 리뷰 내용에서 '- 내용 추가' 방식으로 하위 카테고리를 추가하지 않습니다.",
    "   - 코드 리뷰 내용은 **한 개의 문단으로 유지하며**, 여러 개의 세부 항목으로 분리하지 않습니다.",
    
    "## ✅ 출력 형식:",
    "출력 형식은 반드시 아래의 규칙을 따라야 합니다.",
    
    """
    <Title> 가장 중요한 코드 리뷰 내용을 한 줄 요약합니다.</Title>

    <Review>
    <Content>코드 리뷰 제목</Content>
    <Detail>코드 리뷰 내용 및 상세 설명 (한 문단으로 작성)</Detail>

    <Content>코드 리뷰 제목</Content>
    <Detail>코드 리뷰 내용 및 상세 설명 (한 문단으로 작성)</Detail>

    <Content>코드 리뷰 제목</Content>
    <Detail>코드 리뷰 내용 및 상세 설명 (한 문단으로 작성)</Detail>
    </Review>
    """,

    "## ✅ 출력 형식 규칙:",
    "- **각 코드 리뷰 제목은 핵심적인 알고리즘 개념 및 코드 오류를 반영해야 합니다.**",
    "- 단순히 **'오답 발생'** 같은 표현 대신, **'DFS 탐색 방향 오류로 인해 정답을 찾지 못함'**처럼 구체적인 내용을 포함해야 합니다.",
    "- **코드가 틀렸다면, 정답을 맞출 수 있도록 실질적인 수정 방향을 한 문단으로 제공해야 합니다.**",
    "- **이미 해결된 피드백은 출력하지 않아야 합니다.** ('이 피드백은 해결되었습니다' 같은 문구도 금지)",
    "- **가독성 개선 피드백은 코드가 정답을 도출하는 경우에만 제공하며, 불필요한 가독성 피드백은 금지합니다.**",
    "- **출력의 마지막에 불필요한 결론 요약(예: '따라서', '결론적으로')을 포함하지 않습니다.**",
    "- **'이와 같은 개선을 통해 문제를 더 효율적으로 해결할 수 있습니다.' 같은 마무리 문장을 출력하지 않도록 주의해야 합니다.**",
    "- **코드 리뷰 항목 외에는 불필요한 부가 설명을 출력하지 말고, 오직 핵심 리뷰 내용만 유지해야 합니다.**",
    "- **모든 코드 리뷰 내용은 반드시 한 문단으로 작성해야 하며, 하위 카테고리('- 내용 추가')를 포함해서는 안 됩니다.**",
    "- **출력 형식에서 `<Review>` 태그를 최상위 컨테이너로 유지하며, 각각의 코드 리뷰는 `<Content>`와 `<Detail>`을 사용하여 표현해야 합니다.**"
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
    "유저가 제공한 코드(<풀이코드>)에서 특정 부분을 개선할 수 있도록, 피드백 제목과 피드백 내용을 바탕으로 해당 코드의 시작 줄과 끝 줄을 찾아야 합니다.",
    "시작 줄과 끝 줄은 반드시 명확한 숫자로 지정되어야 하며, 추정값을 사용해서는 안 됩니다.",
    "시작 줄과 끝 줄은 가능한 최소한의 줄 수를 포함해야 합니다.",
    "즉, 피드백 제목과 내용과 관련된 **핵심적인 코드 부분만 선택**하여, 불필요하게 많은 줄을 포함하지 않아야 합니다.",
    
    "## ✅ 줄 번호 찾기 규칙:",
    "1. **피드백과 가장 관련성이 높은 코드 줄을 우선적으로 선택해야 합니다.**",
    "2. **시작 줄과 끝 줄 사이의 간격을 최소화해야 합니다.**",
    "   - 코드 블록(반복문, 조건문, 함수 등)과 관련된 경우, **해당 블록이 끝나는 위치까지만 포함해야 합니다.**",
    "   - 하나의 코드 줄과만 관련이 있는 경우, (X, X)처럼 같은 줄 번호를 시작과 끝으로 설정해야 합니다.",
    "3. **주석이나 불필요한 코드 줄을 포함하지 않도록 해야 합니다.**",
    "4. **코드에서 피드백과 관련성이 낮은 줄을 포함하지 않도록 주의해야 합니다.**",
    
    "## ✅ 출력 형식:",
    "각 피드백 항목은 반드시 다음 형식을 따라야 합니다.",
    
    """
    피드백
    (시작 줄, 끝 줄) 상세한 개선 사항

    예시:

    (5, 10) 반복문을 줄여서 시간 복잡도를 개선할 수 있음. 현재 O(n^2)이므로 O(n log n)으로 최적화 가능.
    (8, 8) 특정 조건문에서 불필요한 검사를 수행함. 조건을 최적화하여 중복 연산을 제거할 수 있음.
    """,
    
    "## ✅ 개선 사항 작성 규칙:",
    "- **피드백 제목을 유지하며**, 해당 줄 범위를 어떻게 개선할지를 한 문단으로 설명해야 합니다.",
    "- **개선 사항은 한 문단으로 작성해야 하며, 불필요한 목록이나 하위 카테고리는 포함하지 않습니다.**",
    "- **코드 수정 예시는 포함하지 않으며, 오직 개선 방향만 설명합니다.**",
    "- **'이와 같은 개선을 통해 문제를 더 효율적으로 해결할 수 있습니다.' 같은 마무리 문장을 절대 포함하지 않습니다.**",
    
    "## ✅ 예제 입력 및 출력 예시:",
    
    "### 🔹 입력 예시:",
    """
    <피드백 제목> 이분 탐색을 활용한 최적화 필요
    <피드백 내용> 현재 코드는 모든 가능한 숙련도 레벨을 1부터 최대 난이도까지 순차적으로 검사하여 제한 시간 내에 퍼즐을 해결할 수 있는 최소한의 숙련도를 찾습니다. 그러나, 난이도 및 퍼즐 개수의 범위가 매우 크기 때문에, 이 접근 방식은 비효율적입니다. 최적의 숙련도를 찾기 위해 이분 탐색을 활용하는 것이 좋습니다. 이분 탐색을 통해 숙련도를 효율적으로 탐색하면, 시간 복잡도를 O(n log m)으로 줄일 수 있습니다. 여기서 n은 퍼즐의 개수이고, m은 난이도의 최대값입니다. 먼저 중간값을 기준으로 현재 숙련도로 퍼즐을 제한 시간 내에 해결할 수 있는지를 검사하고, 가능 여부에 따라 탐색 범위를 조정해 나가면 됩니다.
    
    <풀이코드>
    def find_min_skill(puzzles, max_difficulty):
        min_skill = 1
        while min_skill <= max_difficulty:
            if check_skill(puzzles, min_skill):
                return min_skill
            min_skill += 1
        return -1
    """
    
    "### 🔹 출력 예시:",
    """
    <title>이분 탐색을 활용한 최적화 필요</title>
    (3, 7) 현재 코드는 모든 가능한 숙련도 값을 1부터 최대 난이도까지 선형 탐색하며 검사하지만, 문제의 범위가 크기 때문에 비효율적입니다. 최적화를 위해 이분 탐색을 적용하여 탐색 범위를 절반씩 줄여가면서 최적의 숙련도를 찾아야 합니다. 중간값을 기준으로 퍼즐 해결 가능 여부를 평가한 후, 숙련도를 조정하는 방식이 더 적합합니다.
    """,
    
    "## ✅ 유의 사항:",
    "- 출력 형식에 맞춰 (시작 줄, 끝 줄)을 정확히 표기해야 합니다.",
    "- 시작 줄과 끝 줄 간격을 최소화해야 하며, 가능한 경우 단일 줄만 포함할 수도 있습니다.",
    "- 반드시 피드백 제목을 유지하고, **개선해야 할 내용을 한 문단으로 상세하게 설명해야 합니다.**"
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
        user_input3 = f"<피드백 제목> {title}\n<피드백 내용> {content}\n<문제설명> {prob}\n<풀이코드> {source_code}"
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
