from datetime import datetime
import re
import openai
import os
import json
import xml.etree.ElementTree as ET
from django.conf import settings

# settings.py에서 API 키 불러오기
OPENAI_API_KEY = settings.OPENAI_API_KEY

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
        "   - <풀이 코드>가 틀렸다면, **어떤 부분이 잘못되었는지 분석하고, 올바르게 수정할 방향을 마크다운 형식으로 설명해야 합니다.**",
        "   - 단순히 '오답 발생'이라고 하지 말고, **어떤 개념이 부족한지, 어떤 논리적 오류가 있는지를 구체적으로 서술해야 합니다.**",
        "   - 문제점과 해결 방법이 직접적으로 연결되도록 작성해야 합니다.",
        "   - 문제점 설명에는 '잘못된 조건 사용', '불완전한 탐색 방식' 등 핵심적인 알고리즘적 오류를 포함해야 합니다.",
        "   - 'DFS 탐색 방향 오류' 등 알고리즘의 핵심 개념을 제목에 반영해야 합니다.",

        "3. **최적화 필요 시 개선 방향 제공**",
        "   - 코드가 동작하지만 비효율적이라면, **시간 복잡도 및 공간 복잡도를 비교하며 개선 방법을 제안합니다.**",
        "   - 예를 들어, '현재 O(N^2) 복잡도를 가지므로 이진 탐색을 활용하면 O(log N)으로 개선 가능합니다.' 와 같이 작성해야 합니다.",
        "   - 현재 코드의 시간 복잡도가 O(N^2)이라면, O(N log N)으로 줄일 수 있는 최적화 기법을 명시해야 합니다.",

        "4. **가독성 피드백은 필요할 경우에만 제공**",
        "   - 코드가 **정확하지 않다면**, 가독성 피드백은 제공하지 않습니다. (정확성을 먼저 해결해야 함)",
        "   - 코드가 정확하게 동작하는 경우에만, 변수명 개선, 함수 구조 개선 등의 피드백을 마크다운 형식으로 추가할 수 있습니다.",

        "5. **피드백 제목과 내용 일관성 유지**",
        "   - `<Content>` 태그에는 반드시 **명확한 피드백 제목**만 포함해야 합니다.",
        "   - **문장형 표현(예: '시간 복잡도 개선이 필요합니다.') 대신, 간결한 제목(예: 'DFS 탐색 중복으로 인해 O(N^2) 복잡도 발생')을 사용해야 합니다.**",
        "   - 피드백 제목에는 **알고리즘적 키워드**(DFS, BFS, DP 등)를 포함하여 문제의 본질을 드러내야 합니다.",

        "6. **출력 형식 준수**",
        """
        <Title> 가장 중요한 코드 리뷰 내용을 한 줄 요약합니다.</Title>

        <Review>
        <Content>피드백 제목 (명확한 키워드 사용)</Content>
        <Detail>
        **🔍 현재 코드의 문제점**
        - [문제점 설명 (논리적 오류, 잘못된 조건, 비효율적인 탐색 방식 등)]
        
        **🚀 해결 방법**
        1. **[해결 방법 요약]**
        - [구체적인 해결 방법 설명, 변수나 함수명 언급 가능]
        - [알고리즘 최적화 가능 시, 시간 복잡도 비교 필수]

        **✅ 기대 효과**
        - [개선 이후 기대되는 효과]
        </Detail>

        <Content>피드백 제목 (명확한 키워드 사용)</Content>
        <Detail>
        **🔍 현재 코드의 문제점**
        - [문제점 설명]
        
        **🚀 해결 방법**
        1. **[해결 방법 요약]**
        - [구체적인 해결 방법 설명]
        - [관련된 변수나 함수명 언급 가능]

        **✅ 기대 효과**
        - [개선 이후 기대되는 효과]
        </Detail>
        </Review>
        """,

        "7. **출력 형식 규칙 준수**",
        "- **각 코드 리뷰 제목은 핵심적인 알고리즘 개념 및 코드 오류를 반영해야 합니다.**",
        "- **'오답 발생' 같은 표현 대신, 'DFS 탐색 방향 오류로 인해 정답을 찾지 못함'처럼 구체적인 내용을 포함해야 합니다.**",
        "- **출력의 마지막에 불필요한 결론 요약(예: '따라서', '결론적으로')을 포함하지 않습니다.**",
        "- **가독성 개선 피드백은 코드가 정답을 도출하는 경우에만 제공하며, 불필요한 가독성 피드백은 금지합니다.**",
        "- **출력 형식에서 `<Review>` 태그를 최상위 컨테이너로 유지하며, 각각의 코드 리뷰는 `<Content>`와 `<Detail>`을 사용하여 표현해야 합니다.**",
        "- **출력 내용에 직접적인 코드 블록(````python ... ````)이 포함되지 않아야 합니다.**",
        "- **필요한 경우, 변수명 및 함수명을 언급할 수 있으나 코드의 전체 구조를 직접적으로 제공하지 않습니다.**",
    ]

    return feedback_content

def re_review_system_prompt() :
    rereview_content = [
        "**당신은 사용자가 제공한 이전 피드백과 현재 풀이 코드가 주어졌을 때, 해당 코드가 피드백을 적절히 해결했는지 평가하는 역할을 합니다.**",

        "**🚨 필수 규칙 (절대 어길 수 없음)**\n"
        "1. **출력 시 `<피드백 제목>`은 절대 포함하지 않습니다.**\n"
        "2. **출력은 `<content>`와 `<status>` 태그만 포함해야 합니다. `<title>`을 출력하면 안 됩니다.**\n"
        "3. **출력 시 `<content>`에는 코드 블록이 포함되지 않습니다.**\n"
        "   - **구현 방식은 서술형으로 설명하며, 코드 예시는 제공하지 않습니다.**\n"
        "   - **알고리즘 로직을 설명할 때는 단계별로 상세히 서술해야 합니다.**\n"
        "   - **적절한 줄 바꿈을 추가하여 가독성을 높입니다.**\n",

        "**📌 입력 형식 (반드시 이 형식으로 입력됨)**\n"
        "- `<문제 설명>`: 사용자가 풀려고 한 문제의 설명입니다.\n"
        "- `<풀이 코드>`: 사용자가 현재 작성한 코드입니다.\n"
        "- `<피드백 제목>`: 이전 피드백의 제목입니다.\n"
        "- `<피드백 내용>`: 이전 피드백의 핵심 내용을 포함합니다.\n"
        "- 당신은 `<풀이 코드>`가 `<피드백 내용>`을 적절히 반영했는지를 평가해야 합니다.\n",

        "**📌 평가 방식**\n"
        "- 새로운 피드백을 생성하지 않으며, 기존 피드백이 완수되었는지를 평가합니다.\n"
        "- 완수된 경우 `<status>pass</status>`를 출력하며, 미완수된 경우 `<status>fail</status>`와 함께 부족한 부분을 설명합니다.\n",

        "**📌 출력 형식 (반드시 이 형식으로 출력해야 합니다.)**\n"
        '"""',
        "<content>\n"
        "**👍 칭찬할 점 (pass일 경우)**\n"
        "- 설명...\n\n"
        "**🎯 해결한 점 (pass일 경우 - 자세한 명세 포함)**\n"
        "- 해결 방법 1: 어떤 로직을 통해 문제를 해결했는지 구체적으로 서술\n"
        "- 해결 방법 2: 적용한 알고리즘의 각 단계가 어떤 역할을 하는지 설명\n\n"
        "**✅ 기대 효과**\n"
        "- 기대 효과 1\n"
        "- 기대 효과 2\n"
        "</content>",
        "<status>pass 또는 fail</status>",
        '"""',

        "**📌 `pass` 상태의 출력 기준**\n"
        "- 풀이 코드가 이전 피드백을 완전히 반영했다면 `<status>pass</status>`를 출력합니다.\n"
        "- `<content>`에는 문제점을 지적하는 대신, **잘 해결한 점을 구체적으로 기술**해야 합니다.\n"
        "- **해결한 점은 코드 블록 없이, 로직과 단계별 설명을 포함하여 자세히 서술해야 합니다.**\n"
        "- **이전 코드와의 차이점을 논리적으로 설명하는 내용이 포함되어야 합니다.**\n",

        "**📌 `fail` 상태의 출력 기준**\n"
        "- 풀이 코드가 이전 피드백을 반영하지 못했다면 `<status>fail</status>`를 출력합니다.\n"
        "- `<content>`에는 현재 풀이 코드가 어떻게 부족한지를 상세하게 설명합니다.\n"
        "- **개선 방법은 코드 블록 없이, 로직을 단계별로 설명해야 합니다.**\n"
        "- **어떤 방식으로 개선할 수 있는지, 구체적인 접근 방식을 서술해야 합니다.**\n",

        "**📌 올바른 예시 (`pass` 상태의 경우) (반드시 이 형식으로 출력할 것!)**\n"
        '"""',
        "<content>\n"
        "**👍 칭찬할 점**\n"
        "- 기존 코드에서 BFS를 DFS로 최적화하여 탐색 속도를 향상시켰습니다.\n"
        "- 가독성이 개선되어 유지보수성이 높아졌습니다.\n\n"
        "**🎯 해결한 점**\n"
        "- 기존 BFS 방식에서는 모든 노드를 순차적으로 탐색했으나, DFS 방식에서는 깊이 우선 탐색을 통해 불필요한 경로를 효율적으로 건너뛰었습니다.\n"
        "- DFS의 백트래킹 기능을 활용하여 목표 노드에 도달하지 않는 경로를 조기에 종료시킴으로써 성능을 최적화했습니다.\n"
        "- 탐색 과정에서 방문 여부를 기록하는 방식을 개선하여, 동일한 노드를 중복 방문하는 문제가 발생하지 않도록 했습니다.\n"
        "- 이를 통해 시간 복잡도가 O(N^2)에서 O(N log N)으로 개선되었으며, 메모리 사용량도 절감할 수 있었습니다.\n\n"
        "**✅ 기대 효과**\n"
        "- 대규모 데이터셋에서도 탐색 성능이 안정적으로 유지될 수 있습니다.\n"
        "- 불필요한 계산을 줄여 시스템 리소스를 효율적으로 사용하게 됩니다.\n"
        "</content>",
        "<status>pass</status>",
        '"""',

        "**📌 올바른 예시 (`fail` 상태의 경우) (반드시 이 형식으로 출력할 것!)**\n"
        '"""',
        "<content>\n"
        "**🔍 문제점**\n"
        "- 현재 코드에서 불필요한 반복문이 많아 시간 복잡도가 증가함.\n\n"
        "**🚀 개선 방법**\n"
        "- 반복문을 줄이기 위해 해시맵을 사용하는 방법을 제안합니다.\n"
        "- 해시맵을 사용하면 키-값 쌍을 통해 탐색 시간을 O(1)로 단축할 수 있습니다.\n"
        "- 기존의 이중 반복문을 해시맵으로 대체하면, 탐색 대상 배열을 한 번만 순회하여도 원하는 값을 빠르게 찾아낼 수 있습니다.\n"
        "- 예를 들어, 배열의 값을 해시맵에 저장해두고, 목표 값을 찾을 때 해당 값이 해시맵에 존재하는지 검사하는 방식으로 개선할 수 있습니다.\n"
        "- 이렇게 하면 각 요소에 대해 한 번의 연산만 수행하므로, 전체 시간 복잡도가 O(N^2)에서 O(N)으로 최적화될 수 있습니다.\n\n"
        "**✅ 기대 효과**\n"
        "- 기존 O(N^2) 연산이 O(N)으로 최적화됨.\n"
        "- 대용량 데이터에서도 일관된 성능을 기대할 수 있습니다.\n"
        "</content>",
        "<status>fail</status>",
        '"""'
    ]


    return rereview_content

def lines_system_prompt() :
    algorithm_content = [
        "유저가 제공한 코드(<usercode>)에서 특정 부분을 찾을 수 있도록, <feedback_title>과 <feedback_content>을 바탕으로 해당 코드의 시작 줄과 끝 줄을 찾아야 합니다.",
        "시작 줄과 끝 줄은 반드시 명확한 숫자로 지정되어야 하며, 추정값을 사용해서는 안 됩니다.",
        "시작 줄과 끝 줄은 피드백과 가장 적합한 코드 범위를 포함해야 합니다.",
        "즉, <feedback_title>과 <feedback_content>과 관련된 **핵심적인 코드 부분을 포함**해야 하며, 지나치게 짧거나 불완전한 코드 범위를 선택해서는 안 됩니다.",

        "## ✅ 줄 번호 찾기 규칙:",
        "1. **피드백과 가장 관련성이 높은 코드 줄을 우선적으로 선택해야 합니다.**",
        "2. **<feedback_content>과 가장 적합한 코드 줄을 선택해야 합니다.**",
        "   - 코드 블록(반복문, 조건문, 함수 등)과 관련된 경우, **해당 블록이 끝나는 위치까지 포함해야 합니다.**",
        "   - 하나의 코드 줄과만 관련이 있는 경우라도, **연결된 코드가 있다면 블록 단위로 포함해야 합니다.**",
        "3. **주석이나 불필요한 코드 줄은 포함하지 않도록 해야 합니다.**",
        "4. **조건문(`if`), 반복문(`for`, `while`), 함수(`def`)가 포함된 경우, 해당 블록이 시작되는 줄부터 끝나는 줄까지 포함해야 합니다.**",
        "5. **특정 조건문이나 연산이 함수 내에서 수행되는 경우, 함수의 주요 로직을 포함해야 합니다.**",
        "6. **반복문(`while`, `for`) 내부에서 return이 사용되는 경우, 반복문의 종료(return)까지 포함해야 합니다.**",
        "7. **함수 외부에서 특정 함수를 호출하는 경우, 해당 함수 호출과 결과 처리 로직까지 포함해야 합니다.**",
        "8. **코드의 핵심 연산이 이루어지는 함수가 있다면, 함수의 시작부터 끝까지 포함해야 합니다.**",
        "9. **단순한 초기화 부분(변수 선언, 데이터 구조 생성)과 핵심 로직을 구분하여, 필요 이상의 줄을 포함하지 않도록 주의해야 합니다.**",

        "## ✅ 필수 규칙:",
        "1. **<feedback_title>과 <feedback_content>에 대해 오직 하나의 (시작 줄, 끝 줄)만 반환해야 합니다.**",
        "2. **여러 개의 가능성이 있는 경우, 가장 핵심적인 한 가지를 GPT가 선택해야 합니다.**",
        "   - 코드 성능에 가장 중요한 영향을 미치는 부분을 우선적으로 선택",
        "   - <feedback_content>과 가장 직접적인 관련이 있는 부분을 우선 선택",
        "   - 코드의 논리적 흐름과 관련된 가장 중요한 부분을 우선 선택",
        "3. **여러 개의 (시작 줄, 끝 줄)을 포함하면 안 됩니다.**",

        "## ✅ 출력 형식:",
        "출력은 반드시 다음 형식을 따라야 합니다.",

        """
        <title> "<feedback_title>" </title>
        (시작 줄, 끝 줄) 
        """,

        "## ✅ 유의 사항:",
        "- 반드시 하나의 (시작 줄, 끝 줄)만 포함해야 합니다.",
        "- 시작 줄과 끝 줄을 피드백과 가장 적합한 범위로 설정해야 합니다.",
        "- 피드백 제목은 입력값인 `<feedback_title>`을 그대로 유지해야 합니다.",
        "- 여러 개의 (시작 줄, 끝 줄)을 나열하지 말고, 가장 중요한 하나만 반환해야 합니다."
    ]




    return algorithm_content

def chatbot_system_prompt() -> list:
    """ Return chatbot-service system prompt"""
    return [
        {"role": "system", "content": "당신은 생성된 코드 리뷰 피드백 내용에 대한 질문을 받는 AI입니다. 사용자가 받은 피드백에 대해 이해를 돕는 것이 목적입니다."},
        {"role": "system", "content": "<problem_description>알고리즘 문제에 대한 정보입니다.</problem_description>"},
        {"role": "system", "content": "<solution_code>알고리즘 풀이 코드에 대한 정보입니다.</solution_code>"},
        {"role": "system", "content": "<feedback_topic>GPT 모델에게 받은 피드백 주제에 대한 정보입니다.</feedback_topic>"},
        {"role": "system", "content": "<feedback_content>피드백 주제에 대한 자세한 설명 정보입니다.</feedback_content>"},
        {"role": "system", "content": "<question>사용자가 받은 피드백 중 이해되지 않는 부분이나 관련된 궁금증을 담고 있습니다. 질문을 잘 파악해 친근하고 쉽게 답변하세요.</question>"},
        {"role": "system", "content": "위 형식은 질문을 이해하기 위한 용도이며, 응답에서는 사용하지 않습니다."},

        {"role": "system", "content": "답변 작성 시 규칙:"},
        {"role": "system", "content": "1. **일관성 유지:** 모든 답변은 동일한 톤과 구조를 따릅니다. 사용자가 계속 질문할 때 자연스러운 대화를 유지하세요."},
        {"role": "system", "content": "2. **답변 목적 집중:** 답변은 사용자의 이해를 돕는 데만 집중하세요. 사용자의 풀이 코드나 피드백 내용을 재평가하거나 추가 피드백을 제공하지 마세요."},
        {"role": "system", "content": "3. **답변 구조:** 아래 형식을 기준으로 답변을 작성합니다. 각 상황에 맞게 필요한 부분만 선택하세요.\n- 📝 **간단한 이론 설명:** 개념을 짧고 간결하게 설명합니다.\n- 🔎 **자세한 설명 요청 시:** 추가 세부 정보나 배경 지식을 제공합니다.\n- 💡 **코드 예시 요청 시:** 핵심 코드 1~2줄(최대 10줄 이내)만 코드 블록(\`\`\`)으로 작성합니다. 전체 코드나 정답 코드를 제공하지 않으며, 문제 풀이 중심이 아닌 개념 이해에 중점을 둡니다."},
        {"role": "system", "content": "4. **아이콘 사용 규칙:** 상황에 맞게 다음 아이콘을 사용합니다.\n- 📝 개념 및 이론 설명\n- 🔎 추가 설명 요청 시\n- 💡 코드 예시 제시 시\n- 🚀 기대 효과나 장점 강조 시\n- ⚠️ 주의사항 또는 제한 사항 안내 시"},
        {"role": "system", "content": "5. **문장 작성 규칙:**\n- 짧고 간결한 문장 사용.\n- 글머리 기호(-, *, +)를 사용해 가독성을 높입니다.\n- 문장은 끊어 작성하고, 긴 문장은 나누어 작성하세요."},
        {"role": "system", "content": "6. **사용자 요청별 답변 예시:**\n- 사용자가 알고리즘을 모를 때:\n  📝 **LRU 알고리즘은 \"최소 최근 사용\"을 의미하며, 가장 오랫동안 사용되지 않은 항목을 제거하는 캐시 교체 방식입니다.**\n- 사용자가 자세한 설명을 요청할 때:\n  🔎 **LRU는 캐시 히트 시 해당 항목을 최신 위치로 이동시킵니다. 캐시 미스 시에는 가장 오래된 항목을 제거하고 새 항목을 추가합니다. 이 방식은 메모리 효율성을 높입니다.**\n- 사용자가 코드 예시를 요청할 때:\n  💡 **LRU 동작의 핵심 로직 예시입니다:**\n  ```python\n  if city in cache:\n      cache.move_to_end(city)  # 최근 사용 항목으로 갱신\n  else:\n      if len(cache) == cacheSize:\n          cache.popitem(last=False)  # 가장 오래된 항목 제거\n      cache[city] = True\n  ```\n  ⚠️ 전체 코드가 아닌 핵심 로직만 제공됩니다."},
        {"role": "system", "content": "7. **마크다운 사용 규칙:**\n- **굵은 글씨**와 인라인 코드(\`코드\`)만 사용하세요.\n- *Italic* 기울임, 제목(#, ##, ###) 사용 금지.\n- 표는 사용하지 않습니다."},
        {"role": "system", "content": "8. **마무리 규칙:**\n- 불필요한 결론이나 평가 문구 생략.\n- 자연스럽게 추가 질문을 유도하세요. 예: \"더 궁금한 게 있으면 언제든 물어봐!\""},
        {"role": "system", "content": "9. **언어:** 모든 답변은 한국어로 작성하세요."}
    ]


def success_lines_prompt():
    success_prompt = [
        "당신의 역할은 주어진 코드(`index_code`)에서 <피드백 제목>과 <피드백 내용>이 반영된 줄 번호 범위를 정확히 찾는 것입니다.",
        "코드는 이미 `generate_index_code(source_code)`를 사용하여 `index_code`로 변환되었으며, 줄 번호와 코드가 함께 포함되어 있습니다.",
        "당신은 `index_code`를 분석하여 해당 피드백이 실제로 적용된 줄을 찾아야 합니다.",
        "출력 시 <피드백 제목>과 <피드백 내용>을 그대로 사용하며, 내용을 수정하거나 요약하지 않습니다.",

        "## ✅ 줄 번호 찾기 규칙:",
        "1. **피드백이 적용된 첫 번째 줄과 마지막 줄을 정확하게 찾아야 합니다.**",
        "2. **피드백이 적용된 코드가 함수(`def`), 반복문(`for`, `while`), 조건문(`if`) 등 블록 단위라면, 블록 전체를 포함해야 합니다.**",
        "3. **불필요한 코드(주석, 단순 변수 선언 등)는 포함하지 않습니다.**",
        "4. **피드백의 핵심 변경 사항이 포함된 코드 줄만 선택해야 합니다.**",
        "5. **반복문이나 조건문이 포함된 경우, 해당 블록이 끝나는 줄까지 포함해야 합니다.**",
        "6. **여러 가능성이 있는 경우, 가장 핵심적인 하나만 선택해야 합니다.**",

        "## ✅ 출력 형식:",
        "출력은 반드시 다음 형식을 따라야 합니다.",

        """
    <title> "<피드백 제목>" </title>
    (시작 줄, 끝 줄)
        """,

        "출력 예시는 다음과 같습니다.",

        """
    <title> "이분 탐색 최적화" </title>
    (17, 25)
        """,

        "## ✅ 유의 사항:",
        "- 반드시 하나의 (시작 줄, 끝 줄)만 포함해야 합니다.",
        "- 시작 줄과 끝 줄은 `index_code`에서 피드백이 반영된 부분을 기준으로 정확하게 선택해야 합니다.",
        "- **<피드백 제목>과 <피드백 내용>을 그대로 유지해야 합니다.**",
        "- **줄 번호를 찾는 것이 핵심 목표이며, 코드 설명이나 개선 방법을 추가하지 않습니다.**"
    ]
    return success_prompt


    
########################parse,re_Final_function#############################################
# 주어진 코드 문자열에 줄 번호를 추가하여 index_code를 생성하는 함수.
def generate_index_code(code):
    lines = code.split('\n')  # 코드 줄 단위로 나누기
    index_code = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines)])  # 줄 번호 추가
    return index_code

def description_sc(response):
    """
    response 문자열에서 <content>와 <status> 값을 추출하는 함수
    """
    content_match = re.search(r'<content>(.*?)</content>', response, re.DOTALL)
    status_match = re.search(r'<status>(.*?)</status>', response)

    content = content_match.group(1).strip() if content_match else None
    status = status_match.group(1).strip() if status_match else None

    return content, status

def process_rentest_list(rentest_list):
    fail_list = []
    total_list = []
    pass_list = []

    for title, content, status in rentest_list:
        if status == 'fail':
            fail_list.append([title, content])  # 실패한 경우 fail_list에 추가
        else :
            pass_list.append([title,content])

        total_list.append([title, content, 0, 0, status])  # 모든 항목을 total_list에 추가

    return fail_list, total_list, pass_list

def update_total_list_from_pem_list(pem_list, total_list):
    """
    pem_list에서 (title, new_start_line, new_end_line)을 추출하여 total_list에 반영하는 함수.
    같은 title이 있으면 기존 content와 status를 유지하면서, (new_start_line, new_end_line)만 업데이트.
    """

    # pem_list 순회하며 title, 시작 줄, 끝 줄 추출
    for response in pem_list:
        match = re.search(r'<title>\s*"?([^"]*?)"?\s*</title>\s*\((\d+),\s*(\d+)\)', response, re.DOTALL | re.MULTILINE)

        if match:
            title = match.group(1).strip()  # 피드백 제목 추출 (큰따옴표 제거)
            new_start_line = int(match.group(2))  # 새로운 시작 줄
            new_end_line = int(match.group(3))  # 새로운 끝 줄

            # total_list에서 해당 title 찾기 (큰따옴표 제거)
            for i, (existing_title, existing_content, start_line, end_line, status) in enumerate(total_list):
                if existing_title.strip('"') == title:  # 큰따옴표 유무 고려하여 비교
                    # 같은 title이 있으면 줄 번호만 업데이트
                    total_list[i] = [existing_title, existing_content, new_start_line, new_end_line, status]
                    break  # 한 번 업데이트하면 루프 종료

    return total_list

def convert_status_to_boolean(final_list):
    """
    final_list에서 pass/fail을 True/False로 변환하는 함수
    """
    updated_list = [[title, content, start_line, end_line, status == 'pass'] for title, content, start_line, end_line, status in final_list]
    
    return updated_list


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

def chat3_with_gpt(prompt, mark_content):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": msg} for msg in mark_content] + [
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

    # 🔹 정규 표현식에서 대소문자를 무시하도록 `(?i)` 추가
    contents = re.findall(r'(?i)<content>(.*?)</content>', content_response, re.DOTALL)
    details = re.findall(r'(?i)<detail>(.*?)</detail>', content_response, re.DOTALL)

    # [[<content>, <detail>], [<content>, <detail>], ...] 형태로 리스트 생성
    result = [[content.strip(), detail.strip()] for content, detail in zip(contents, details)]

    maybe_feedback = []
    line_content = lines_system_prompt()
    index_code = generate_index_code(source_code)

    caution = """
✅ caution :
    - 반드시 하나의 (시작 줄, 끝 줄) 개선 사항만 출력해야 합니다.
    - 만약 여러 개의 가능성이 있는 경우, 가장 핵심적인 한 가지를 GPT가 선택하여 출력해야 합니다.
    - 여러 개의 (시작 줄, 끝 줄) 개선 사항을 나열하지 말고, 오직 하나만 출력하세요.
"""
        
    for title, content in result:
        user_input3 = f"<feedback_title>{title}</feedback_title>\n<feedback_content> {content}</feedback_content>\n<problem> {prob}</problem>\n<usercode> {index_code}</usercode>\n <caution> {caution}"
        response = chat2_with_gpt(user_input3, line_content)
        maybe_feedback.append(response)

    # 최종 결과를 저장할 리스트
    final_list = []
    temp_list = []

    # 각 피드백을 순회하며 (시작 줄, 끝 줄) 추출
    for (title, content), feedback in zip(result, maybe_feedback):
        match = re.search(r"\((\d+),\s*(\d+)\)", feedback)  # (시작 줄, 끝 줄)만 추출
        if match:
            start_line, end_line = match.groups()
            temp_list.append([title,content])  
            final_list.append([title, content, int(start_line), int(end_line), False]) 

    return final_list if final_list else []


#################################################################################
# "reviews"에서 [title,content]로 이루어진 리스트 previous_feedback
def generate_re_review(prob,source_code,reviews) :
    previous_list = [(review["title"], review["comments"]) for review in reviews]
    # previous_feedback = f'"""\n{json.dumps(previous_list, indent=4, ensure_ascii=False)}\n"""'
    rentest_list = list()

    index_code = generate_index_code(source_code)

    re_review_content = re_review_system_prompt()
    for title, content in previous_list : 
        user_input2 = f"<문제 설명> {prob}</문제 설명>\n<풀이 코드> {index_code}</풀이 코드>\n<피드백 제목>{title}</피드백 제목>\n<피드백 내용>{content}</피드백 내용>"
        response = chat_with_gpt(user_input2,re_review_content)
        new_content, new_status = description_sc(response)
        rentest_list.append([title,new_content,new_status])

    fail_list, total_list,pass_list = process_rentest_list(rentest_list)

    tem_list = list()
    line_content = lines_system_prompt()
    
    caution = """
    ✅ 주의 사항:
        - 반드시 하나의 (시작 줄, 끝 줄) 개선 사항만 출력해야 합니다.
        - 만약 여러 개의 가능성이 있는 경우, 가장 핵심적인 한 가지를 GPT가 선택하여 출력해야 합니다.
        - 여러 개의 (시작 줄, 끝 줄) 개선 사항을 나열하지 말고, 오직 하나만 출력하세요.
    """
    for i in range(len(fail_list)) :
        user_input4 = "<feedback_title>"+fail_list[i][0] + "</feedback_title>" + "\n"+ "<feedback_content>" + fail_list[i][1] + "</feedback_content>"+ "\n" + "<problem>" + prob + "</problem>" +"\n" + "<usercode>" + index_code +"</usercode>" +"\n" + "<주의사항>"+ caution
        response = chat2_with_gpt(user_input4, line_content)
        tem_list.append(response)

    ## 성공한 피드백
    pem_list = list()
    sucess_prompt = success_lines_prompt()
    for i in range(len(pass_list)) : 
        user_input5 = "<피드백 제목>"+ pass_list[i][0] + "</피드백 제목>" +"\n"+ "<피드백 내용>" + pass_list[i][1] + "</피드백 내용>" + "\n" + "<문제설명>" + prob + "</문제설명>" + "\n" + "<풀이코드>" + index_code + "</풀이코드>" +"\n" + caution
        response = chat2_with_gpt(user_input5, sucess_prompt)
        pem_list.append(response)
    
    medium_list = update_total_list_from_pem_list(tem_list, total_list)
    final_list = update_total_list_from_pem_list(pem_list, medium_list)

    updated_final_list = convert_status_to_boolean(final_list)
    final_list.clear()
    final_list = updated_final_list

    return final_list if final_list else []

# final_list = generate_ai_review(prob, source_code,problem_info)

#################################################################################
#########################Main Function###########################################
def generate_ai_review(prob : str, source_code : str, reviews : list) : 
    if len(reviews) > 0 :
        result = generate_re_review(prob,source_code,reviews)
    else :
        result = generate_review(prob,source_code)

    if result is None:
        result = []     

    return result

def generate_chatbot(request_data: dict) -> str:
    messages = chatbot_system_prompt()

    # 기존 대화 이력을 포함하여 모델에게 전달
    for q, r in zip(request_data["questions"], request_data["answers"]):
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": r})

    messages.append({
        "role": "user",
        "content": (
            f"<problem_description>\n{request_data['problem_info']}\n</problem_description>\n\n"
            f"<solution_code>\n{request_data['source_code']}\n</solution_code>\n\n"
            f"<feedback_topic>\n{request_data['review_info']['title']}\n</feedback_topic>\n\n"
            f"<feedback_content>\n{request_data['review_info']['comments']}\n</feedback_content>\n\n"
            f"<question>\n{request_data['questions'][-1]}\n</question>\n\n"
        )
    })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=600
        )
        
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
        "당신은 코드 최적화를 전문으로 하는 AI 엔지니어입니다.",
        "사용자가 제공한 코드(<code>)는 <prob>을 해결하기 위해 작성되었습니다.",
        "사용자는 FINAL_LIST의 피드백을 반영하여 최적화된 최종 코드(Final Code)를 원합니다.",
        
        "## 입력 데이터 설명",
        "1. <문제 설명>: 문제의 설명이 포함됩니다.",
        "2. <풀이 코드>: 사용자가 작성한 기존 코드입니다.",
        "3. <FINAL_LIST>: 코드에서 개선이 필요한 부분과 수정 방향을 제공합니다.",
        """   - 형식: `[피드백 제목, 피드백 내용, 시작 줄 번호, 끝 줄 번호]`",
            - '시작 줄 번호'와 '끝 줄 번호'는 **기존 코드에서 수정이 필요한 영역을 지정**합니다.""",
        
        "## 코드 수정 지침",
        "1. **FINAL_LIST의 피드백을 반영하여 필요한 부분만 변경**",
        """   - 피드백에 지정된 줄 번호(시작 줄 ~ 끝 줄)를 기준으로 수정합니다.",
            - **단, 최적화된 코드에서 수정된 줄 번호는 기존 코드와 다를 수 있습니다.**",
            - 최적화 과정에서 **줄 수가 변경될 경우 새로운 줄 번호를 자동으로 반영**해야 합니다.""",
        
        "2. **코드 성능과 가독성 개선**",
        """   - 불필요한 변수 및 중복 로직을 제거하고, 최적의 알고리즘을 적용합니다.",
            - 코드의 유지보수성을 높이기 위해 가독성을 고려합니다.""",
        
        "3. **불필요한 변경은 하지 않음**",
        """   - 피드백이 없는 코드 부분은 변경하지 않습니다.",
            - 코드 스타일을 불필요하게 변경하지 않고, 원래의 흐름을 유지합니다.""",
        
        "## 출력 형식",
        "최적화된 최종 코드만 출력해야 합니다.",
        "출력 형식은 다음과 같습니다:",
        """
        <code>
        최적화된 코드
        </code>
        <lines>
            <line>
                <title>피드백 제목</title>
                <start_line>최적화된 코드에서의 시작 줄 번호</start_line>
                <end_line>최적화된 코드에서의 끝 줄 번호</end_line>
            </line>
            <line>
                <title>피드백 제목</title>
                <start_line>최적화된 코드에서의 시작 줄 번호</start_line>
                <end_line>최적화된 코드에서의 끝 줄 번호</end_line>
            </line>
            ...
        </lines>
        """
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

def generate_solution_code(problem_info : str , source_code : str, reviews : list) :

    final_list = [(review["title"], review["comments"],review["start_line_number"],review["end_line_number"]) for review in reviews]
    final_feedback = f'"""{json.dumps(final_list)}"""'

    prob = problem_info
    index_code = generate_index_code(source_code)

    solution_prompt = solution_system_prompt ()
    user_input3 = "<문제 설명>" + prob + "\n" + "<풀이 코드>" + index_code + "\n" + "<FINAL_LIST>" + final_feedback
    code_response = chat3_with_gpt(user_input3,solution_prompt)

    # 🔹 프로그래밍 코드 추출 (XML 시작 전까지 텍스트를 코드로 간주)
    code_match = re.search(r"^(.*?)(?=\n<lines>)", code_response, re.DOTALL)
    markdown_code = code_match.group(1).strip() if code_match else "No Code Found"
    middle_lines = markdown_code.splitlines()
    solution_lines = middle_lines[1:-1]
    solution_code = "\n".join(solution_lines)

    # 🔹 XML 데이터 추출
    xml_match = re.search(r"<lines>(.*?)</lines>", code_response, re.DOTALL)
    solution_xml = f"<lines>{xml_match.group(1)}</lines>" if xml_match else "No Lines Found"

    # 🔹 XML을 파싱하여 solution_list 생성
    solution_list = []
    if "No Lines Found" not in solution_xml:  # XML 데이터가 존재하는 경우만 처리
        root = ET.fromstring(solution_xml)
        for line in root.findall(".//line"):
            title = line.find("title").text
            start_line = int(line.find("start_line").text) - 1
            end_line = int(line.find("end_line").text) - 1
            solution_list.append([title, start_line, end_line])

    return solution_code, solution_list
