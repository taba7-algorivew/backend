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
        "문제 설명은 prob이며, 재풀이 코드(source_code)는 새롭게 제출된 풀이 코드입니다. Previous Feedback은 [<피드백 제목>, <피드백 내용>]의 리스트로 나열되었습니다.",
        "새로운 피드백을 생성하지 않으며, 이전 피드백이 완수되었는지를 평가합니다.",
        "완수된 경우 해당 피드백을 제외하며, 미완수된 경우 <피드백 제목>은 유지하되, <피드백 내용>에 현재 풀이 코드에서 어떤 부분이 부족한지를 설명합니다.",
        "평가 결과를 다음 형식으로 제공합니다.",
        '"""',
        "<title><피드백 제목></title>",
        "<content><피드백 내용></content>",
        "<status>pass 또는 fail</status>",
        '"""',
        "문제를 성공한 경우 <status>pass</status>, 실패한 경우 <status>fail</status>를 출력합니다."
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
        
        "## ✅ 필수 규칙 (수정됨):",
        "1. **각 피드백 제목과 피드백 내용에 대해 오직 하나의 (시작 줄, 끝 줄) 개선 사항만 반환해야 합니다.**",
        "2. **여러 개의 개선 가능 영역이 있을 경우, GPT가 판단하여 가장 핵심적인 한 가지를 선택해야 합니다.**",
        "   - 코드 성능에 가장 중요한 영향을 미치는 부분을 우선적으로 선택",
        "   - 피드백 내용과 가장 직접적인 관련이 있는 부분을 우선 선택",
        "   - 코드의 논리적 흐름을 개선하는 데 가장 중요한 부분을 우선 선택",
        "3. **선택된 개선 사항만 반환해야 하며, 여러 개의 (시작 줄, 끝 줄)을 포함하면 안 됩니다.**",
        
        "## ✅ 출력 형식:",
        "각 피드백 항목은 반드시 다음 형식을 따라야 합니다.",
        
        """
        <title> 피드백 제목 </title>
        (시작 줄, 끝 줄) 상세한 개선 사항

        예시:

        <title>이분 탐색을 활용한 최적화 필요</title>
        (3, 7) 현재 코드는 모든 가능한 숙련도 값을 1부터 최대 난이도까지 선형 탐색하며 검사하지만, 문제의 범위가 크기 때문에 비효율적입니다. 최적화를 위해 이분 탐색을 적용하여 탐색 범위를 절반씩 줄여가면서 최적의 숙련도를 찾아야 합니다. 중간값을 기준으로 퍼즐 해결 가능 여부를 평가한 후, 숙련도를 조정하는 방식이 더 적합합니다.
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
        """,
        
        "### 🔹 출력 예시:",
        """
        <title>이분 탐색을 활용한 최적화 필요</title>
        (3, 7) 현재 코드는 모든 가능한 숙련도 값을 1부터 최대 난이도까지 선형 탐색하며 검사하지만, 문제의 범위가 크기 때문에 비효율적입니다. 최적화를 위해 이분 탐색을 적용하여 탐색 범위를 절반씩 줄여가면서 최적의 숙련도를 찾아야 합니다. 중간값을 기준으로 퍼즐 해결 가능 여부를 평가한 후, 숙련도를 조정하는 방식이 더 적합합니다.
        """,
        
        "## ✅ 유의 사항:",
        "- 출력 형식에 맞춰 (시작 줄, 끝 줄)을 정확히 표기해야 합니다.",
        "- 시작 줄과 끝 줄 간격을 최소화해야 하며, 가능한 경우 단일 줄만 포함할 수도 있습니다.",
        "- 반드시 피드백 제목을 유지하고, **개선해야 할 내용을 한 문단으로 상세하게 설명해야 합니다.**",
        "- **여러 개의 (시작 줄, 끝 줄)을 나열하지 말고, 가장 중요한 하나만 반환해야 합니다.**"
    ]


    return algorithm_content

def chatbot_system_prompt() -> list:
    """챗봇 시스템 프롬프트 반환"""
    return [
        {"role": "system", "content": "당신은 생성된 코드 리뷰 피드백 내용에 대한 질문을 받는 AI입니다. 사용자가 받은 피드백에 대해 이해를 돕는 것이 목적입니다."},
        {"role": "system", "content": "< 문제 설명 >은 알고리즘 문제에 대한 정보입니다."},
        {"role": "system", "content": "< 풀이 코드 >은 알고리즘 풀이 코드에 대한 정보입니다."},
        {"role": "system", "content": "< 피드백 주제 >은 GPT 모델에게 받은 피드백 주제에 대한 정보입니다."},
        {"role": "system", "content": "< 피드백 내용 >은 피드백 주제에 대한 자세한 설명 정보입니다."},
        {"role": "system", "content": "< 질문 >은 사용자가 받은 피드백 중 이해되지 않는 부분이나 관련된 궁금증을 담고 있습니다. 질문을 잘 파악해 친근하고 쉽게 답변하세요."},
        {"role": "system", "content": "위 형식은 질문을 이해하기 위한 용도이며, 응답에서는 사용하지 않습니다."},
        {"role": "system", "content": "답변 작성 시 규칙:"},
        {"role": "system", "content": "1. 마크다운 표기를 사용할 수 있으나 제목(#, ##, ###)은 사용하지 않습니다."},
        {"role": "system", "content": "2. 강조(**Bold**, *Italic*), 글머리 기호(-, *, +), 번호 목록(1., 2., 3.)은 사용할 수 있습니다."},
        {"role": "system", "content": "3. 코드 블록(```) 표기는 사용할 수 있으나, 전체 코드를 작성하지 말고 핵심 코드 조각만 간단히 보여주세요."},
        {"role": "system", "content": "4. 불필요한 마무리 피드백은 작성하지 마세요. 대신 사용자가 더 물어볼 수 있도록 친근하게 마무리하세요."},
        {"role": "system", "content": "5. 답변은 너무 길지 않게, 필요한 만큼만 작성하세요."},
        {"role": "system", "content": "6. 친구가 설명하듯 편안하고 친근한 어투를 사용하세요."},
        {"role": "system", "content": "7. 한국어로 답하세요."}
    ]

def markdown_system_prompt() :
    read_content = [
        "**당신은 사용자가 제공하는 피드백 내용을 가독성 높은 형식으로 변환하는 역할을 합니다.**",

        "**🔹 기본 규칙**\n"
        "1. **<피드백 제목>은 변경하지 않습니다.**\n"
        "2. **<피드백 내용>을 읽고 다음과 같은 방식으로 변환합니다:**\n"
        "   - 긴 문단을 의미 단위로 나누어 보기 쉽게 정리합니다.\n"
        "   - **리스트 (`- 내용`)** 를 사용하여 정보를 나열합니다.\n"
        "   - 순서가 중요한 경우 **번호 (`1.`, `2.`)** 를 사용합니다.\n"
        "   - 논리적 구분이 필요한 경우 **소제목** 을 추가합니다.\n"
        "   - **강조 (`**텍스트**`)** 를 사용하여 핵심 개념을 강조합니다.\n"
        "   - **코드 블록** 을 사용하여 시간 복잡도 및 알고리즘 설명을 가독성 있게 정리합니다.\n"
        "   - 적절한 **줄 바꿈** 을 추가하여 내용이 한눈에 들어오도록 합니다.\n",

        "**🔹 변환 예시**\n"
        "**입력:**\n"
        "```\n"
        "<피드백 제목> 이분 탐색을 사용하여 시간 복잡도를 개선해야 합니다.\n"
        "<피드백 내용> 현재 코드는 숙련도를 최대 난이도부터 차례대로 감소시키면서 제한 시간 내에 퍼즐을 해결할 수 있는지 확인하는 방식으로 수행되고 있습니다. "
        "이 접근 방식은 최악의 경우 O(max(diffs) * n)의 시간 복잡도를 가지며, diffs의 최대값이 100,000인 상황에서 매우 비효율적일 수 있습니다. "
        "이를 개선하기 위해 이분 탐색을 사용하여 숙련도의 최솟값을 효율적으로 찾도록 해야 합니다. "
        "이분 탐색을 적용하면, 숙련도의 범위를 반씩 줄여가며 각 단계에서 제한 시간 내에 퍼즐을 해결할 수 있는지를 확인할 수 있으며, "
        "이를 통해 시간 복잡도를 O(n log(max(diffs)))로 줄일 수 있습니다. "
        "이 방식은 숙련도의 중간값을 기준으로 퍼즐 해결 가능 여부를 판단하고, 그 결과에 따라 탐색 범위를 조정하는 방식으로 진행됩니다.\n"
        "```\n\n",

        "**출력:**\n"
        "```\n"
        "<title>**이분 탐색을 사용하여 시간 복잡도를 개선해야 합니다.**</title>\n\n"
        "<content>"
        "**🔍 현재 코드의 문제점**\n"
        "- 숙련도를 최대 난이도부터 감소시키며 퍼즐 해결 가능 여부를 검사하는 방식.\n"
        "- 최악의 경우 **O(max(diffs) * n)** 의 시간 복잡도를 가짐.\n"
        "- `diffs`의 최대값이 **100,000**일 때 비효율적.\n\n"
        "**🚀 해결 방법: 이분 탐색 적용**\n"
        "1. **이분 탐색을 통해 숙련도의 최솟값을 찾음**  \n"
        "   - 숙련도의 중간값을 기준으로 퍼즐 해결 가능 여부를 판단.  \n"
        "   - 결과에 따라 탐색 범위를 조정하여 최적의 숙련도를 찾음.\n\n"
        "2. **시간 복잡도 개선**  \n"
        "   - 기존 방식: **O(max(diffs) * n)**  \n"
        "   - 이분 탐색 적용 후: **O(n log(max(diffs)))**  \n"
        "   - 탐색 범위를 반씩 줄여 더 빠르게 결과 도출 가능.\n\n"
        "**✅ 기대 효과**\n"
        "- 기존 방식 대비 **더 빠른 연산 속도**.\n"
        "- `max(diffs)`가 큰 경우에도 **효율적으로 동작**.\n"
        "</context>"

        "```"
    ]
    return read_content


    
########################parse,re_Final_function#############################################
def parse_response_with_lines(response):
    matches = re.finditer(r'<title>(.*?)</title>\s*<content>(.*?)</content>\s*<status>(pass|fail)</status>', response, re.DOTALL)
    
    lines_list = []
    total_list = []
    
    for match in matches:
        title = match.group(1).strip()
        content = match.group(2).strip()
        status = match.group(3).strip().lower()
        
        status_flag = True if status == 'pass' else False
        start_line = 0  # 실제 라인 번호를 찾는 로직이 필요하면 추가 가능
        end_line = 0    # 실제 라인 번호를 찾는 로직이 필요하면 추가 가능
        
        total_list.append([title, content, start_line, end_line, status_flag])
        
        if not status_flag:
            lines_list.append([title, content])
    
    return lines_list, total_list

def create_final_list(total_list, fail_feedback):
    final_list = []
    feedback_data = {}
    
    for feedback in fail_feedback:
        match = re.search(r'<title>(.*?)</title>\s*\((\d+),\s*(\d+)\)\s*(.*?)$', feedback, re.DOTALL | re.MULTILINE)
        if match:
            title = match.group(1).strip()
            start_line = int(match.group(2))
            end_line = int(match.group(3))
            content = match.group(4).strip()
            feedback_data[title] = (content, start_line, end_line)
    
    for item in total_list:
        title, content, start_line, end_line, status = item
        
        if title in feedback_data and not status:  # fail인 경우 업데이트
            new_content, new_start, new_end = feedback_data[title]
            final_list.append([title, new_content, new_start, new_end, status])
        else:
            final_list.append(item)
    
    return final_list

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



########################review, re_review function #########################################

def generate_review(prob,source_code) :
    review_content = review_system_prompt()

    user_input = f"<문제 설명> {prob}\n<풀이 코드> {source_code}"

    content_response = chat_with_gpt(user_input, review_content)

        # 정규 표현식을 사용하여 <Content>와 <Detail> 태그 안의 내용을 추출
    contents = re.findall(r'<Content>(.*?)</Content>', content_response, re.DOTALL)
    details = re.findall(r'<Detail>(.*?)</Detail>', content_response, re.DOTALL)

    # [[<Content>, <Detail>], [<Content>, <Detail>], ...] 형태로 리스트 생성
    result = [[content.strip(), detail.strip()] for content, detail in zip(contents, details)]

    # 각 번호별 내용을 저장할 리스트
    title_list = []

    title_list = re.findall(r'<Content>(.*?)</Content>', content_response, re.DOTALL)

    maybe_feedback = []
    line_content = lines_system_prompt()

    caution = """
✅ caution :
    - 반드시 하나의 (시작 줄, 끝 줄) 개선 사항만 출력해야 합니다.
    - 만약 여러 개의 가능성이 있는 경우, 가장 핵심적인 한 가지를 GPT가 선택하여 출력해야 합니다.
    - 여러 개의 (시작 줄, 끝 줄) 개선 사항을 나열하지 말고, 오직 하나만 출력하세요.
"""
        
    for title, content in result:
        user_input3 = f"<피드백 제목> {title}\n<피드백 내용> {content}\n<문제설명> {prob}\n<풀이코드> {source_code}\n <caution> {caution}"
        response = chat2_with_gpt(user_input3, line_content)
        maybe_feedback.append(response)

    final_list = []
    temp_list = []
    for (title, feedback) in zip([t.strip("*") for t, _ in result], maybe_feedback):
        match = re.search(r"\((\d+),\s*(\d+)\)\s*(.*)", feedback, re.DOTALL)
        if match:
            start_line, end_line, content = match.groups()
            temp_list.append([title, content.strip()])
            final_list.append([title, content.strip(), int(start_line), int(end_line),False])

    markdown_prompt = markdown_system_prompt()
    contest_list = list()
    for title,content in temp_list :
        user_mark = f"<피드백 제목>{title} \n<피드백 내용>{content}"
        response = chat2_with_gpt(user_mark,markdown_prompt)
        contest_list.append([title,response])
    temp_list.clear()

        # 정제된 contest_list를 저장할 리스트
    cleaned_contest_list = []

    # content를 마크다운이 적용된 형태로 정제
    for title, content in contest_list:
        cleaned_content = content.replace("```", "").strip()  # 불필요한 ``` 제거
        cleaned_content = re.sub(r"</?content>", "", cleaned_content).strip()  # <content> 태그 제거
        cleaned_contest_list.append([title, cleaned_content])  # 새로운 리스트에 저장

    contest_list.clear()
    contest_list = cleaned_contest_list

    # content_list를 딕셔너리로 변환 (title -> good_content)
    content_dict = {title: good_content for title, good_content in contest_list}

    # final_list 업데이트
    for item in final_list:
        title = item[0]  # 현재 title
        if title in content_dict:  # 정제된 content가 존재하는 경우
            item[1] = content_dict[title]  # content 업데이트`

    return final_list if final_list else []
    
# "reviews"에서 [title,content]로 이루어진 리스트 previous_feedback
def generate_re_review(prob,source_code,reviews) :


    previous_list = [(review["title"], review["comments"]) for review in reviews]
    previous_feedback = f'"""\n{json.dumps(previous_list, indent=4, ensure_ascii=False)}\n"""'

    re_review_content = re_review_system_prompt()

    user_input2 = f"<문제 설명> {prob}\n<풀이 코드> {source_code}\n<previous_feedback>{previous_feedback}"

    re_content_response = chat_with_gpt(user_input2,re_review_content)

    lines_list, total_list = parse_response_with_lines(re_content_response)

    fail_feedback = list()
    line_content = lines_system_prompt()
    caution = """
    ✅ 주의 사항:
        - 반드시 하나의 (시작 줄, 끝 줄) 개선 사항만 출력해야 합니다.
        - 만약 여러 개의 가능성이 있는 경우, 가장 핵심적인 한 가지를 GPT가 선택하여 출력해야 합니다.
        - 여러 개의 (시작 줄, 끝 줄) 개선 사항을 나열하지 말고, 오직 하나만 출력하세요.
    """
    for i in range(len(lines_list)) :
        user_input4 = "<피드백 제목>"+lines_list[i][0] + "\n"+ "<피드백 내용>" + lines_list[i][1] + "\n" + "<문제설명>" + prob + "\n" + "<풀이코드>" + source_code + "\n" + caution
        response = chat2_with_gpt(user_input4, line_content)
        fail_feedback.append(response)


    final_list = create_final_list(total_list, fail_feedback)

    

    return final_list
# final_list = generate_ai_review(prob, source_code,problem_info)

#########################Main Function###################################################
def generate_ai_review(prob : str, source_code : str, reviews : list) : 
    
    if reviews :
        result = generate_re_review(prob,source_code,reviews)
    else :
        result = generate_review(prob,source_code)

    if result is None:
        result = []     

    return result

def generate_chatbot(request_data: dict) -> str:
    messages = chatbot_system_prompt()

    for q, r in zip(request_data["questions"], request_data["answers"]):
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": r})

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
            max_tokens=600
        )

        # ✅ 수정된 부분: ["content"] 대신 .content 속성 사용
        chatbot_response = response.choices[0].message.content  

        if not chatbot_response:
            print("⚠️ OpenAI 응답이 비어 있음!")
            return "죄송합니다. 현재 답변을 생성할 수 없습니다."

        return chatbot_response
    except openai.OpenAIError as e:
        print(f"OpenAI API Error: {str(e)}")
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        print(f"Internal Server Error: {str(e)}")
        return f"Internal Server Error: {str(e)}"

### 모범답안

def solution_system_prompt () :
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

def chat3_with_gpt(prompt,solution_prompt):
    response = response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
   *[{"role": "system", "content": msg} for msg in solution_prompt],
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


def generate_solution_code(problem_info : str , source_code : str, reviews : list) -> str :

    final_list = [(review["title"], review["comments"],review["start_line_number"],review["end_line_number"]) for review in reviews]
    final_feedback = f'"""{json.dumps(final_list)}"""'

    prob = problem_info

    solution_prompt = solution_system_prompt ()
    user_input3 = "<문제 설명>" + prob + "\n" + "<풀이 코드>" + source_code + "\n" + "<FINAL_LIST>" + final_feedback
    code_response = chat3_with_gpt(user_input3,solution_prompt)

    return code_response


