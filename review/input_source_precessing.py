# web_req.py
import requests
from bs4 import BeautifulSoup as BS
import google.generativeai as genai
import os
import json
from PIL import Image, UnidentifiedImageError
import io
from django.conf import settings

MAX_TRIES = 3    # MAX Request problem info
GENAI_API_KEY = settings.GENAI_API_KEY

def get_the_url(url) :
    if 'programmers' in url :
        crawler= Programmers(url)
    elif 'acmicpc' in url :
        crawler= Acmicpc(url)
    else :
        return {
            "status": False, 
            "message": "not support url"}
    
    if crawler.status == True :
        return {
            "status" : True, 
            "title": crawler.title, 
            "content": crawler.content,
        }
    else :
        return {"status": False, "message": "문제 url을 확인해주세요."}
    
class ProblemResponse:
    def __init__(self, status=False, title="", description=""):
        self.status = status
        self.title = title
        self.description = description

    def to_dict(self):
        return {
            "status": self.status,
            "title": self.title,
            "description": self.description
        }
        
class Manager :
    def __init__(self, url) :
        self.url = url
        self.get_page()
        if self.status :
            self.find_problem_data()
        
    def get_page(self):
        # 최대 시도 수 설정
        max_tries= MAX_TRIES
        for i in range(max_tries) :
            is_success= False
            try :
                header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
                r = requests.get(self.url, headers = header)
                # 요청 성공 여부 확인
                if r.status_code == 200 :
                    is_success= True
                    self.page= BS(r.text, features="html.parser")
                    break
                else :
                    print(f"요청 {i+1}회 실패, {self.url}")
                    raise
            except :
                continue
        if is_success :
            self.status= True
        else :
            self.status= False
            
    def find_problem_data(self) :
        raise NotImplementedError()
            

    

class Programmers(Manager) :
    def __init__(self, url) :
        super().__init__(url)
        
    def find_problem_data(self) :
        self.content= self.page.find(id="tour2").find("div", {"class": "markdown"}).text
        self.title= self.page.find("span", {"class": "challenge-title"}).text
            

class Acmicpc(Manager) :
    def __init__(self, url) :
        super().__init__(url)
        
    def find_problem_data(self) :
        self.content= self.page.find(id="problem-body").text
        self.title= self.page.find(id="problem_title").text
        
        
        
class NotSupportSite(Exception) :
    pass

def fetch_problem_from_image(image):
    """AI 모델을 호출하여 이미지에서 문제 정보를 생성하는 함수"""
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-lite-preview-02-05")

    response = model.generate_content([
        "이 이미지는 알고리즘 문제를 찾아내는 이미지입니다.",
        "이미지에 있는 문제 정보를 추적해 답변해주세요.",
        "입력 형식, 출력 형식, 예제는 모두 하나의 문제 정보로 취급하세요.",
        "문제 정보를 추출할 때 적절하게 줄바꿈 표기를 해주세요",
        "항상 다음과 같은 형식으로 JSON으로 출력을 보내주세요: { 'status': True, 'title': '문제 제목', 'description': '문제 설명' }",
        "응답은 한국어로 해야 합니다.",
        image  # 원본 이미지 전달
    ])

    return response.text if response.text else None

def get_info_img(image_bytes):
    """이미지에서 문제 정보를 분석하고 추출하는 함수"""
    if not GENAI_API_KEY:
        return ProblemResponse(description="Missing API Key").to_dict()

    try:
        image = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError:
        return ProblemResponse(description="Invalid image").to_dict()
    except Exception:
        return ProblemResponse(description="Invalid image").to_dict()

    # AI 모델 호출 및 응답 검증
    for attempt in range(MAX_TRIES):
        raw_text = fetch_problem_from_image(image)

        if raw_text is None:
            return ProblemResponse(description="API request failed").to_dict()

        try:
            problem_data = json.loads(raw_text)

            if all(key in problem_data for key in ["status", "title", "description"]):
                return problem_data
        except json.JSONDecodeError:
            pass

    return ProblemResponse(description="Invalid API response after multiple attempts").to_dict()
