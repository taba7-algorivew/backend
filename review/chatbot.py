import openai
import os

# OpenAI API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

openai.api_key = OPENAI_API_KEY

def chatbot_prompts() -> list:
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

def chatbot_service(request_data: dict) -> str:
    messages = chatbot_prompts()    # 프롬프트 불러오기

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

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=800
    )

    return response.choices[0].message.content