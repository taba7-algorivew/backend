# web_req.py
import requests
from bs4 import BeautifulSoup as BS

MAX_TRIES= 3

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
            "description": crawler.description,
        }
    else :
        return {"status": False, "message": "문제 url을 확인해주세요."}
        
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
        self.description= self.page.find(id="tour2").find("div", {"class": "markdown"}).text
        self.title= self.page.find("span", {"class": "challenge-title"}).text
            

class Acmicpc(Manager) :
    def __init__(self, url) :
        super().__init__(url)
        
    def find_problem_data(self) :
        self.description= self.page.find(id="problem-body").text
        self.title= self.page.find(id="problem_title").text
        
        
        
class NotSupportSite(Exception) :
    pass

def get_info_img(image) :
    return {"status": False, "message": "아직 미구현"}