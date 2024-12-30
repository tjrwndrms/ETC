import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, UnexpectedAlertPresentException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
import logging
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 최신 버전의 크롬 사용자 에이전트 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

# 크롬 옵션 설정
options = Options()
options.add_argument("disable-infobars")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--remote-debugging-port=9222")
options.add_argument(f"user-agent={user_agent}")
options.add_argument("--user-data-dir=C:/Temp/ChromeProfile")  # 사용자 데이터 디렉토리 지정
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# 웹 드라이버 초기화
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 탐지 방지 스크립트 실행
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')  # .env에서 API 키를 가져옴
)

time_x = 700

time.sleep(1)

csv_file = 'C:\\Users\\ssm\\Desktop\\aha\\output.csv'

# 'utf-8' 인코딩으로 CSV 파일 읽기
df = pd.read_csv(csv_file, encoding='utf-8')

time.sleep(random.randint(2, 6))

def check_answer(title, contents):
    while True:
        try:
            print('\ncheck_answer_ making')
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=f" 아래 질문을 친절한 대화체로 수정해. 정리된 웹 페이지 글 형식으로 작성해. 아래 질문을 친절한 대화체로 수정해. 말투를 바꿔서 60글자 이상으로 바꿔줘. 친절한 대화체로 작성해줘. (안녕하세요. 고수님들에게 물어볼 점 있어 이곳에 글을 적습니다.)로 시작해. \n 질문: {title}{contents}",
                temperature=0.7,
                max_tokens=3000
            )
            print()
            if len((response.choices[0].text.strip()).replace(" ", "")) <= 55:
                print("\n리턴값이 공백 제외 55자 이하입니다. 처음부터 다시 시작합니다.")
                continue

            else:
                return response.choices[0].text.strip()
            
        except Exception as e:
                print(f"\n예외 발생: {e}")
                if 'tokens' in str(e):
                    return 'tokens error'
                else:
                    continue

def make_title(title, contents):
    while True:
        try:
            print('\nmake_title')

            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=f"아래 질문을 보고 적절한 제목을 16~20자로 만들어. 다른말은 필요없이 적절한 제목을 괄호()안에 넣어. 아래 질문을 보고 적절한 제목을 16~20자로 만들어. \n 질문: {title}{contents}",
                temperature=0.7,
                max_tokens=3000
            )
            # Extracting the made title from the response
            made_title = response.choices[0].text.strip()
            made_title = made_title.replace("(", "")
            made_title = made_title.replace(")", "")
            made_title = made_title.replace("\"", "")

            if len(made_title.replace(" ", "")) <= 15:
                print("\n리턴값이 공백 제외 15자 이하입니다. 처음부터 다시 시작합니다.")
                continue
            else:
                return made_title

        except Exception as e:
            print(f"\n예외 발생: {e}")
            if 'tokens' in str(e):
                return 'tokens error'
            else:
                continue

while True:
    
        
    # 웹 페이지 열기
    driver.get('https://a-ha.io/questions/create')
    
    # 무작위 행 선택
    random_row = df.sample()

    # 3번째 열 값 확인 (Python은 0부터 인덱싱하므로 '2'를 사용)
    if pd.isnull(random_row.iloc[0, 2]):
        # 1번째와 2번째 열 값 출력
        title = random_row.iloc[0, 0]  # 1번째 열 값
        contents = random_row.iloc[0, 1]  # 2번째 열 값
        
        # title 또는 contents가 nan인 경우 건너뛰기
        if pd.isnull(title) or pd.isnull(contents):
            print("title 또는 contents가 nan입니다. 다음 행을 선택합니다.")
            continue

        # 'done'을 문자열로 변환하여 특정 행에 추가
        df.loc[random_row.index, 'new_column'] = 'done'  # 특정 행에 'done' 추가

        # 변경된 DataFrame을 다시 CSV 파일로 저장
        df.to_csv('csv_file', index=False)

        time.sleep(5)
        print('수정전')
        print(f'\n{title}')
        print(f'\n{contents}')
        
        print('######################')
        print('######################')

        if len(contents.replace(" ", "")) <= 54:
            contents = check_answer(title, contents)
        
        if len(title.replace(" ", "")) <= 15:
            title = make_title(title, contents)
        
        print('수정후')
        print(f'\n{title}')
        print(f'\n{contents}')
        
        time.sleep(random.randint(2, 6))

    
        # 랜덤 지연 시간 추가 함수
        def random_delay(min_delay=2, max_delay=5):
            time.sleep(random.uniform(min_delay, max_delay))

        try:
            # 제목 입력
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="물음표로 끝나는 제목을 입력해 주세요."]'))
            )
            title_input.send_keys(title)
            
        except TimeoutException:
            print("제목 입력 필드를 찾지 못했습니다.")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue
        
        random_delay()

        try:
            # 내용 입력
            content_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
            )
            content_input.click()  # Div 클릭
            content_input.send_keys(contents)
        except TimeoutException:
            print("내용 입력 필드를 찾지 못했습니다.")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue
        
        random_delay()

        try:
            # '다음' 버튼 활성화까지 대기 (조건부 대기)
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-7xrr51.eqh89qr0'))
            )
            next_button.click()
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"'다음' 버튼을 클릭할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue
        
        random_delay()

        try:
            # '원하시는 토픽이 없다면' 버튼 활성화까지 대기 (조건부 대기)
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-1vtbp04.e4oszzm0'))
            )

            # 버튼 클릭
            button.click()
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"'원하시는 토픽이 없다면' 버튼을 클릭할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue
        
        random_delay()

        try:
            # 입력 필드 활성화까지 대기
            input_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.css-cqkkbz.ebd3d62'))
            )

            # 입력 필드에 't' 입력
            input_field.send_keys('t')
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"입력 필드에 't'를 입력할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue

        random_delay()

        try:
            # '생활꿀팁' 버튼 활성화까지 대기 (조건부 대기)
            living_tip_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'label.css-l8ttje.eguh2g10'))
            )

            # 버튼 클릭
            living_tip_button.click()
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"'생활꿀팁' 버튼을 클릭할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue

        random_delay()

        try:
            # '확인' 버튼 활성화까지 대기 (조건부 대기)
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-usbiy2.eqh89qr0'))
            )

            # '확인' 버튼 클릭
            confirm_button.click()
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"'확인' 버튼을 클릭할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue

        random_delay()

        try:
            # '질문 올리기' 버튼 활성화까지 대기 (조건부 대기)
            submit_question_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-7xrr51.eqh89qr0'))
            )

            # '질문 올리기' 버튼 클릭
            submit_question_button.click()
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"'질문 올리기' 버튼을 클릭할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue

        random_delay()

        try:
            # '답변이 달리면 알려주세요!' 텍스트 포함한 엘리먼트 활성화까지 대기 (조건부 대기)
            notify_me_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[text()="답변이 달리면 알려주세요!"]'))
            )

            # '답변이 달리면 알려주세요!' 엘리먼트 클릭
            notify_me_button.click()
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"'답변이 달리면 알려주세요!' 엘리먼트를 클릭할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue

        random_delay()

        try:
            # '확인' 버튼 활성화까지 대기 (조건부 대기)
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-usbiy2.eqh89qr0'))
            )

            # '확인' 버튼 클릭
            confirm_button.click()
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"'확인' 버튼을 클릭할 수 없습니다: {e}")
            continue
        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Unexpected alert dismissed.")
            except NoAlertPresentException:
                print("No alert present.")
            continue

        random_delay(500, 800)
        
    else:
        continue
