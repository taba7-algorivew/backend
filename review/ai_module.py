from datetime import datetime
import re
import openai
import os
import json
import xml.etree.ElementTree as ET

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
        "**당신은 사용자가 제공한 이전 피드백과 현재 풀이 코드가 주어졌을 때, 해당 코드가 피드백을 적절히 해결했는지 평가하는 역할을 합니다.**",
        
        "**🚨 필수 규칙 (절대 어길 수 없음)**\n"
        "1. **출력 시 `<피드백 제목>`은 절대 포함하지 않습니다.**\n"
        "2. **출력은 `<content>`와 `<status>` 태그만 포함해야 합니다. `<title>`을 출력하면 안 됩니다.**\n"
        "3. **출력 시 `<content>` 내용은 반드시 하나의 단락으로 작성해야 합니다.**\n"
        "   - **문제점, 해결 방법, 기대 효과 등을 여러 개의 문장으로 나누지 말고 하나의 단락에 포함해야 합니다.**\n"
        "   - **여러 개의 문단으로 나누지 마십시오.**\n"
        "   - **예외 없이 하나의 단락으로 유지해야 합니다.**\n",

        "**📌 평가 방식**\n"
        "- 새로운 피드백을 생성하지 않으며, 기존 피드백이 완수되었는지를 평가합니다.\n"
        "- 완수된 경우 해당 피드백을 제외하며, 미완수된 경우 <피드백 제목>과 <피드백 내용>에 기반하여 현재 풀이 코드에서 어떤 부분이 부족한지를 설명합니다.\n",

        "**📌 출력 형식 (반드시 이 형식으로 출력해야 합니다.)**\n"
        '"""',
        "<content>comment</content>",
        "<status>pass 또는 fail</status>",
        '"""',

        "**📌 `pass` 상태의 출력 기준**\n"
        "- 풀이 코드가 이전 피드백을 완전히 반영했다면 `<status>pass</status>`를 출력합니다.\n"
        "- `<content>`에는 풀이 코드가 적절하게 개선되었다는 칭찬 또는 공감의 피드백을 제공합니다.\n"
        "- `pass`일 때, `<content>`는 한 문단으로 작성되어야 합니다.\n",

        "**📌 `fail` 상태의 출력 기준**\n"
        "- 풀이 코드가 이전 피드백을 반영하지 못했다면 `<status>fail</status>`를 출력합니다.\n"
        "- `<content>`에는 현재 풀이 코드가 어떻게 부족한지를 상세하게 설명합니다.\n"
        "- `fail`일 때, `<content>`는 반드시 한 문단이어야 하며, 문제점, 해결 방법, 기대 효과 등을 포함해야 합니다.\n",

        "**📌 잘못된 예시 (이런 방식으로 출력하면 안 됩니다!)**\n"
        '"""',
        "<title>이분 탐색 최적화</title>",
        "<content>\n"
        "**🔍 문제점:** 현재 BFS 알고리즘은 비효율적으로 동작합니다.\n"
        "**🚀 해결 방법:** DFS를 사용하면 성능이 개선될 수 있습니다.\n"
        "**✅ 기대 효과:** O(N^2)에서 O(N log N)으로 개선됩니다.\n"
        "</content>",
        "<status>fail</status>",
        '"""',

        "**📌 올바른 예시 (반드시 이 형식으로 출력할 것!)**\n"
        '"""',
        "<content>현재 BFS 알고리즘은 비효율적으로 동작합니다. DFS를 사용하면 성능이 개선될 수 있으며, 이를 통해 O(N^2)에서 O(N log N)으로 최적화할 수 있습니다.</content>",
        "<status>fail</status>",
        '"""',

        "**📌 추가 유의 사항**\n"
        "- `<content>` 내용은 GPT가 직접 요약하거나 재해석하지 말고, 사용자가 입력한 피드백과 풀이 코드에 기반하여 직접 평가해야 합니다.\n"
        "- `<status>`는 오직 `pass` 또는 `fail`로만 출력해야 합니다.\n"
        "- `fail`일 경우, 단순한 개선 필요성만 서술하지 말고, 구체적인 문제점과 개선 방법을 포함해야 합니다.\n"
    ]


    return correct_content

def lines_system_prompt() :
    algorithm_content = [
        "유저가 제공한 코드(<풀이코드>)에서 특정 부분을 개선할 수 있도록, 피드백 제목과 피드백 내용을 바탕으로 해당 코드의 시작 줄과 끝 줄을 찾아야 합니다.",
        "시작 줄과 끝 줄은 반드시 명확한 숫자로 지정되어야 하며, 추정값을 사용해서는 안 됩니다.",
        "시작 줄과 끝 줄은 피드백과 가장 적합한 코드 범위를 포함해야 합니다.",
        "즉, 피드백 제목과 내용과 관련된 **핵심적인 코드 부분을 포함**해야 하며, 지나치게 짧거나 불완전한 코드 범위를 선택해서는 안 됩니다.",

        "## ✅ 줄 번호 찾기 규칙:",
        "1. **피드백과 가장 관련성이 높은 코드 줄을 우선적으로 선택해야 합니다.**",
        "2. **피드백 내용과 가장 적합한 코드 줄을 선택해야 합니다.**",
        "   - 코드 블록(반복문, 조건문, 함수 등)과 관련된 경우, **해당 블록이 끝나는 위치까지 포함해야 합니다.**",
        "   - 하나의 코드 줄과만 관련이 있는 경우라도, **연결된 코드가 있다면 블록 단위로 포함해야 합니다.**",
        "3. **주석이나 불필요한 코드 줄은 포함하지 않도록 해야 합니다.**",
        "4. **코드에서 피드백과 직접적인 연관성이 높은 부분을 우선적으로 선택해야 합니다.**",
        "5. **조건문(`if`), 반복문(`for`, `while`), 함수(`def`)가 포함된 경우, 해당 블록이 시작되는 줄부터 끝나는 줄까지 포함해야 합니다.**",
        "6. **특정 조건문이나 연산이 함수 내에서 수행되는 경우, 함수의 주요 로직을 포함해야 합니다.**",
        "7. **반복문(`while`, `for`) 내부에서 return이 사용되는 경우, 반복문의 종료(return)까지 포함해야 합니다.**",
        "8. **함수 외부에서 특정 함수를 호출하는 경우, 해당 함수 호출과 결과 처리 로직까지 포함해야 합니다.**",
        "9. **코드의 핵심 연산이 이루어지는 함수가 있다면, 함수의 시작부터 끝까지 포함해야 합니다.**",
        "10. **단순한 초기화 부분(변수 선언, 데이터 구조 생성)과 핵심 로직을 구분하여, 필요 이상의 줄을 포함하지 않도록 주의해야 합니다.**",

        "## ✅ 필수 규칙:",
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
        (61, 63) 현재 코드는 모든 가능한 숙련도 값을 1부터 최대 난이도까지 선형 탐색하며 검사하지만, 문제의 범위가 크기 때문에 비효율적입니다. 최적화를 위해 이분 탐색을 적용하여 탐색 범위를 절반씩 줄여가면서 최적의 숙련도를 찾아야 합니다. 중간값을 기준으로 퍼즐 해결 가능 여부를 평가한 후, 숙련도를 조정하는 방식이 더 적합합니다.
        """,

        "## ✅ 개선 사항 작성 규칙:",
        "- **피드백 제목을 유지하며**, 해당 줄 범위를 어떻게 개선할지를 한 문단으로 설명해야 합니다.",
        "- **개선 사항은 한 문단으로 작성해야 하며, 불필요한 목록이나 하위 카테고리는 포함하지 않습니다.**",
        "- **코드 수정 예시는 포함하지 않으며, 오직 개선 방향만 설명합니다.**",
        "- **'이와 같은 개선을 통해 문제를 더 효율적으로 해결할 수 있습니다.' 같은 마무리 문장을 절대 포함하지 않습니다.**",

        "## ✅ 유의 사항:",
        "- 출력 형식에 맞춰 (시작 줄, 끝 줄)을 정확히 표기해야 합니다.",
        "- 시작 줄과 끝 줄을 피드백과 가장 적합한 범위로 설정해야 합니다.",
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
        {"role": "system", "content": "1. 답변은 반드시 질문에 대한 설명과 이해를 돕는 데만 집중하세요. 사용자의 풀이 코드나 피드백 내용을 다시 평가하거나 추가 피드백을 제공하지 마세요."},
        {"role": "system", "content": "2. 답변은 간결하고 핵심적인 내용을 중심으로 작성하세요. 긴 문장을 피하고, 문장마다 끊어 작성하세요."},
        {"role": "system", "content": "3. 글머리 기호(-, *, +)와 짧은 문장을 사용해 가독성을 높이세요."},
        {"role": "system", "content": "4. 사용자가 '자세히', '구체적으로', '더 알려줘'라는 요청을 명시하지 않는 한, 기본적으로 간단한 설명을 유지하세요."},
        {"role": "system", "content": "5. 사용자가 코드 예시를 요청할 때, 전체 코드나 모범답안을 제공하지 마세요. 대신 문제 해결에 필요한 핵심 코드 조각만 코드 블록(\"```\") 안에 작성하세요."},
        {"role": "system", "content": "6. 코드 예시가 필요한 경우, 기존 사용자의 풀이 코드를 수정하거나 정답처럼 보이게 작성하지 마세요. 단순히 개념 이해를 돕기 위한 최소한의 코드 예시만 작성하세요."},
        {"role": "system", "content": "7. 마크다운 표기 사용 시 다음 규칙을 따르세요: \n   - **강조(Bold)**와 인라인 코드(``코드``)만 사용할 수 있습니다.\n   - *Italic*과 같은 기울임 표기는 사용하지 마세요.\n   - 글머리 기호(-, *, +), 번호 목록(1., 2., 3.)은 사용할 수 있으나, 제목(#, ##, ###)은 사용하지 않습니다."},
        {"role": "system", "content": "8. 불필요한 마무리 피드백이나 코드에 대한 평가를 작성하지 마세요. 대신 사용자가 더 물어볼 수 있도록 자연스럽게 끝맺으세요."},
        {"role": "system", "content": "9. 친구가 설명하듯 편안하고 친근한 어투를 사용하되, 문장과 표현의 일관성을 유지하세요."},
        {"role": "system", "content": "10. 긴 문장이 생성될 경우, 글머리 기호로 나누어 간결한 형태로 답변하세요. 예시나 설명이 길어질 때도 한 문장씩 끊어 작성하여 가독성을 유지하세요."},
        {"role": "system", "content": "11. 한국어로 답하세요."}
    ]

def markdown_system_prompt() :
    read_content = [
        "**당신은 사용자가 제공하는 피드백 내용을 가독성 높은 형식으로 변환하는 역할을 합니다.**",
        
        "**🚨 중요한 규칙 (절대 어길 수 없음)**\n"
        "1. **출력 시 `<피드백 제목>`과 `<피드백 내용>`이라는 단어가 포함되어서는 안 됩니다.**\n"
        "2. **출력 시 `<피드백 제목>`(title) 자체를 포함해서는 안 됩니다.**\n"
        "3. **오직 가독성 높은 `<피드백 내용>`(content) 부분만 출력해야 합니다.**\n"
        "4. **마크다운 문법을 적용하여 내용을 더욱 보기 쉽게 정리합니다.**\n"
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

        "**출력:** (절대 `<피드백 제목>`을 포함하지 말 것!)\n"
        "```\n"
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
        "```"
    ]

    return read_content

def sucess_lines_prompt() :
    success_prompt = [
        "당신의 역할은 주어진 코드(`index_code`)가 <피드백 제목>과 <피드백 내용>에서 제시된 요구 사항을 성공적으로 해결한 부분이 어디인지 찾아내는 것입니다.",
        "코드는 이미 `generate_index_code(source_code)`를 사용하여 `index_code`로 변환되었으며, 줄 번호와 코드가 함께 포함되어 있습니다.",
        "당신은 `index_code`를 분석하여 해당 피드백이 반영된 정확한 줄 번호 범위를 찾아야 합니다.",
        "출력은 반드시 지정된 형식으로 이루어져야 하며, 형식에서 벗어난 출력은 허용되지 않습니다.",
        "피드백이 반영된 부분을 찾을 때, 해당 변경이 정확히 어떤 코드에서 이루어졌는지를 분석하여 줄 번호를 결정해야 합니다.",
        "출력 시 <피드백 제목>과 <피드백 내용>을 그대로 사용하며, 내용을 요약하거나 재구성하지 않습니다.",
        "출력 형식은 다음과 같다",
        """
    <title> 피드백 제목 </title>
    (시작 줄, 끝 줄) 피드백 내용
        """,
        "출력 예시는 다음과 같다",
        """
    <title> 이분 탐색 최적화 </title>
    (17, 25) 기존에는 이분 탐색의 범위 설정이 비효율적이었으나, 최적의 mid 값을 조정하는 로직이 개선되어 더 정확한 결과를 도출할 수 있습니다.
        """,
        "줄 번호(`시작 줄, 끝 줄`)는 반드시 `index_code`에서 피드백이 반영된 부분의 첫 번째 줄과 마지막 줄을 정확하게 찾아야 합니다.",
        "단순히 `코드가 개선되었습니다.`라고 하지 말고, 어떤 점이 개선되었는지를 명확하게 설명해야 합니다.",
        "출력 결과는 한 줄 공백 없이 연속된 형식으로 제공되어야 합니다.",
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

def update_total_list_from_tem_list(tem_list, total_list):
    """
    tem_list에 있는 정보를 추출하여 total_list에 반영하는 함수.
    같은 title이 있으면 new_content와 (new_start_line, new_end_line)을 업데이트함.
    """
    for response in tem_list:
        # 정규식을 사용하여 title, (new_start_line, new_end_line), new_content 추출
        match = re.search(r'<title>(.*?)</title>\s*\((\d+),\s*(\d+)\)\s*(.*)', response, re.DOTALL | re.MULTILINE)

        if match:
            title = match.group(1).strip()
            new_start_line = int(match.group(2))
            new_end_line = int(match.group(3))
            new_content = match.group(4).strip()

            # total_list 업데이트
            for i, item in enumerate(total_list):
                existing_title, existing_content, start_line, end_line, status = item
                
                if existing_title == title:
                    # 같은 title이 있으면 업데이트
                    total_list[i] = [title, new_content, new_start_line, new_end_line, status]
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
    index_code = generate_index_code(source_code)

    caution = """
✅ caution :
    - 반드시 하나의 (시작 줄, 끝 줄) 개선 사항만 출력해야 합니다.
    - 만약 여러 개의 가능성이 있는 경우, 가장 핵심적인 한 가지를 GPT가 선택하여 출력해야 합니다.
    - 여러 개의 (시작 줄, 끝 줄) 개선 사항을 나열하지 말고, 오직 하나만 출력하세요.
"""
        
    for title, content in result:
        user_input3 = f"<피드백 제목> {title}\n<피드백 내용> {content}\n<문제설명> {prob}\n<풀이코드> {index_code}\n <caution> {caution}"
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
            item[1] = content_dict[title]  # content 업데이트

    return final_list if final_list else []


#################################################################################
# "reviews"에서 [title,content]로 이루어진 리스트 previous_feedback
def generate_re_review(prob,source_code,reviews) :


    previous_list = [(review["title"], review["comments"]) for review in reviews]
    # previous_feedback = f'"""\n{json.dumps(previous_list, indent=4, ensure_ascii=False)}\n"""'
    rentest_list = list()

    re_review_content = re_review_system_prompt()
    for title, content in previous_list : 
        user_input2 = f"<문제 설명> {prob}\n<풀이 코드> {source_code}\n<피드백 제목>{title}\n<피드백 내용>{content}"
        response = chat_with_gpt(user_input2,re_review_content)
        new_content, new_status = description_sc(response)
        rentest_list.append([title,new_content,new_status])

    fail_list, total_list,pass_list = process_rentest_list(rentest_list)

    tem_list = list()
    line_content = lines_system_prompt()
    index_code = generate_index_code(source_code)
    caution = """
    ✅ 주의 사항:
        - 반드시 하나의 (시작 줄, 끝 줄) 개선 사항만 출력해야 합니다.
        - 만약 여러 개의 가능성이 있는 경우, 가장 핵심적인 한 가지를 GPT가 선택하여 출력해야 합니다.
        - 여러 개의 (시작 줄, 끝 줄) 개선 사항을 나열하지 말고, 오직 하나만 출력하세요.
    """
    for i in range(len(fail_list)) :
        user_input4 = "<피드백 제목>"+fail_list[i][0] + "\n"+ "<피드백 내용>" + fail_list[i][1] + "\n" + "<문제설명>" + prob + "\n" + "<풀이코드>" + index_code + "\n" + "<주의사항>"+ caution
        response = chat2_with_gpt(user_input4, line_content)
        tem_list.append(response)

    ## 성공한 피드백
    pem_list = list()
    sucess_prompt = sucess_lines_prompt()
    for i in range(len(pass_list)) : 
        user_input5 = "<피드백 제목>"+ pass_list[i][0] + "\n"+ "<피드백 내용>" + pass_list[i][1] + "\n" + "<문제설명>" + prob + "\n" + "<풀이코드>" + index_code + "\n" + caution
        response = chat2_with_gpt(user_input5, sucess_prompt)
        pem_list.append(response)
    
    medium_list = update_total_list_from_tem_list(tem_list, total_list)
    final_list = update_total_list_from_tem_list(pem_list, medium_list)


    updated_final_list = convert_status_to_boolean(final_list)
    final_list.clear()
    final_list = updated_final_list

    temp_list = [[title, content] for title, content, _, _, _ in final_list]

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
            item[1] = content_dict[title]  # content 업데이트

    

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


def generate_solution_code(problem_info : str , source_code : str, reviews : list) -> str :

    final_list = [(review["title"], review["comments"],review["start_line_number"],review["end_line_number"]) for review in reviews]
    final_feedback = f'"""{json.dumps(final_list)}"""'

    prob = problem_info
    index_code = generate_index_code(source_code)

    solution_prompt = solution_system_prompt ()
    user_input3 = "<문제 설명>" + prob + "\n" + "<풀이 코드>" + index_code + "\n" + "<FINAL_LIST>" + final_feedback
    code_response = chat3_with_gpt(user_input3,solution_prompt)

    # 🔹 정규식을 사용하여 Python 코드 (solution_code) 추출
    # - 첫 번째 백틱이 없는 경우도 처리할 수 있도록 수정
    code_match = re.search(r"(?:```python\n|python\n)(.*?)(?:\n```|\n<lines>)", code_response, re.DOTALL)
    solution_code = code_match.group(1).strip() if code_match else ""

    # 🔹 정규식을 사용하여 XML 데이터 (solution_xml) 추출
    xml_match = re.search(r"<lines>(.*?)</lines>", code_response, re.DOTALL)
    solution_xml = f"<lines>{xml_match.group(1)}</lines>" if xml_match else ""

    # 🔹 XML을 파싱하여 solution_list 생성
    solution_list = []
    if solution_xml:
        root = ET.fromstring(solution_xml)
        for line in root.findall(".//line"):
            title = line.find("title").text
            start_line = int(line.find("start_line").text)
            end_line = int(line.find("end_line").text)
            solution_list.append([title, start_line, end_line])

    # 🔹 결과 출력
    print("=== Extracted Solution Code ===")
    print(solution_code)
    print("\n=== Extracted XML (solution_list) ===")
    print(solution_list)

    return solution_code,solution_list


