import discord
import requests
import tempfile
import os
import random
import asyncio
from redbot.core import commands
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# ChromeDriver 경로 설정
chrome_driver_path = "C:\\Users\\ktkim\\Desktop\\FDD\\tts\\chromedriver-win64\\chromedriver.exe"

class TTS(commands.Cog):
    """Text-to-Speech Command for Redbot"""

    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()  # TTS 요청을 위한 큐
        self.is_playing = False  # 현재 재생 중인지 확인
        self.driver = self.init_driver()  # WebDriver 인스턴스 초기화
        self.bot.loop.create_task(self.process_queue())  # 큐 처리 시작
        self.voice_types = []  # 인스턴스 변수 초기화
        self.current_voice = '랜덤'  # 현재 음성 설정
        self.last_voice = None  # 마지막 사용된 목소리 유형 초기화
        self.last_text = None  # 마지막 사용된 텍스트 초기화
        self.last_wav_file_path = None

        # Initialize voice types after WebDriver initialization
        asyncio.create_task(self.get_voice_types(bot.get_context(self.bot.user)))  # Add this line

    def init_driver(self):
        """WebDriver 초기화 (Cog 인스턴스 생성 시 한 번만 호출)"""
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--mute-audio")
        options.add_argument("--headless")  # GUI 숨기기
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        driver.set_window_size(1200, 800)
        url = "https://app.typecast.ai/ko/anonymous-audio-editor?category=firstvisit_ko_live"
        driver.get(url)
        return driver

    async def process_queue(self):
        """큐에서 요청을 처리하는 메서드"""
        while True:
            ctx, user_input = await self.queue.get()  # 큐에서 요청 가져오기
            retry_count = 0
            success = False

            while retry_count < 3 and not success:
                try:
                    if user_input.lower().startswith('add '):
                        add_input = user_input[4:]  # 'add ' 이후의 텍스트
                        await self.handle_add_request(ctx, add_input)  # 'tts add' 요청 처리
                    else:
                        # 사용자 입력 분석
                        voice_type, input_text = await self.analyze_user_input(user_input)

                        # 300자 넘는 경우 나누어서 처리
                        while len(input_text) > 300:
                            part_text = input_text[:300]  # 처음 300자
                            await self.handle_tts_request(ctx, voice_type, part_text)  # 첫 번째 부분 재생
                            input_text = input_text[300:]  # 나머지 부분

                        # 나머지 텍스트 재생
                        if input_text:
                            await self.handle_tts_request(ctx, voice_type, input_text)
                    success = True  # 성공적으로 처리되었음을 표시
                except Exception as e:
                    print(f"오류 발생: {e} | 재시도 중... ({retry_count + 1}/3)")
                    retry_count += 1
                    self.driver.get("https://app.typecast.ai/ko/anonymous-audio-editor?category=firstvisit_ko_live")  # URL로 이동

            self.queue.task_done()  # 작업 완료 표시

    @commands.command(name="tts")
    async def tts_command(self, ctx, *, user_input: str):
        """TTS 명령어: 주어진 텍스트를 음성으로 변환하여 음성 채널에서 재생합니다.
        
        사용법: !tts [목소리 종류] [텍스트]
        예: !tts 호빈 안녕하세요
        
        사용 가능한 목소리 종류:
        - 호빈 / 찬구 / 지윤
        - 진우 / 베리 / 랜덤
        
        'exit' 입력 시 TTS 세션이 종료됩니다.
        """
        # exit 처리
        if user_input.lower() == 'exit':
            # 재생 큐 초기화
            if hasattr(self, 'play_queue'):
                self.play_queue.clear()
            
            # 음성 채널에서 나가기
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            
            # await ctx.send("TTS 세션이 종료되었습니다. 음성 채널에서 나갔습니다.")
            return
            
        # WebDriver가 종료되었는지 확인 및 재초기화
        if self.driver is None:
            self.driver = self.init_driver()  # 새로운 드라이버 초기화
        else:
            try:
                # 간단한 테스트를 통해 드라이버가 여전히 유효한지 확인
                self.driver.current_url  # 유효성 검사
            except Exception:
                self.driver.quit()  # 현재 드라이버 종료
                self.driver = self.init_driver()  # 새로운 드라이버 초기화

        # 큐에 요청 추가
        await self.queue.put((ctx, user_input))
        # await ctx.send(f"TTS 요청이 큐에 추가되었습니다: {user_input}")

    async def get_voice_types(self, ctx):
        """웹 페이지에서 목소리 종류 텍스트를 모두 가져오는 메서드."""
        try:
            # 목소리 종류 요소를 img 태그가 포함된 div 요소만 찾음
            voice_elements = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'tw-flex tw-items-center') and .//img]")
                )
            )

            # 중복을 제거하기 위해 set 자료구조 사용
            voice_types = set()
            for element in voice_elements:
                voice_name = element.find_element(By.CLASS_NAME, "t-body2").text.strip()
                if voice_name:
                    voice_types.add(voice_name)

            self.voice_types = sorted(voice_types)

        except Exception as e:
            await print(f"목소리 종류를 가져오는 중 오류 발생: {e}")

    async def click_element(self, locator: tuple):
        """주어진 locator에 해당하는 요소를 클릭하는 메서드."""
        # 요소를 클릭 가능할 때까지 기다림
        element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(locator))
        await asyncio.sleep(0)  # 잠시 대기
        element.click()  # 요소 클릭 (await 없이 호출)
        print(f"눌렀습니다: {locator}")  # locator 포함

    async def handle_tts_request(self, ctx, voice_type: str, input_text: str):
        """사용자가 입력한 내용을 TTS로 변환하여 재생하는 메서드"""
        wav_file_path = None

        # voice_type -> 재생할 음성
        # current_voice -> 음성 설정
        # last_voice -> 마지막으로 재생한 음성

        try:
            # 사용자 음성 채널 확인
            if ctx.author.voice and ctx.author.voice.channel:
                voice_channel = ctx.author.voice.channel
                if ctx.voice_client and ctx.voice_client.channel == voice_channel:
                    # await ctx.send("이미 음성 채널에 들어와 있습니다. 다른 작업을 진행합니다.")
                    pass
                else:
                    await voice_channel.connect()

                # 음성 유형 가져오기
                await self.get_voice_types(ctx)  # 여기에 추가

                # 이전 목소리와 텍스트가 동일할 경우
                if getattr(self, "last_voice", None) == voice_type and getattr(self, "last_text", None) == input_text:
                    if self.last_wav_file_path:
                        print(f"Current Voice: {self.current_voice}, Last Voice: {self.last_voice}, Last Text: {self.last_text}")
                        await self.play_audio(ctx, self.last_wav_file_path)
                        return
                else:
                    self.last_voice = voice_type
                    self.last_text = input_text
                
                # await ctx.send(f"Current Voice: {self.current_voice}, Last Voice: {self.last_voice}, Last Text: {self.last_text}")
                print(f"Current Voice: {self.current_voice}, Last Voice: {self.last_voice}, Last Text: {self.last_text}")

                # 목소리 종류 클릭
                await self.click_element((By.XPATH, 
                f"//div[contains(text(), '{voice_type}')]"))  # XPATH를 동적으로 생성하여 요소 클릭

                # 텍스트 수정
                await self.modify_text(input_text)

                
                self.driver.execute_script("performance.clearResourceTimings();")

                # 플레이 버튼 클릭
                await self.click_element((By.XPATH, 
                "//div[contains(@class, 'player-bar-play-button')]//div[contains(@class, 'play-button')]"))
                
                # .wav 파일 찾기
                wav_url = await self.find_wav_file(ctx)
                if not wav_url:
                    return

                # 플레이 버튼 클릭
                await self.click_element((By.XPATH, 
                "//div[contains(@class, 'player-bar-play-button')]//div[contains(@class, 'play-button')]"))

                # .wav 파일 다운로드 (고유한 이름으로 생성)
                wav_file_path = await self.download_wav_file(ctx, wav_url)  # wav_file_path 저장
                if not wav_file_path:
                    return

                # 이전 wav_file_path 저장
                self.last_wav_file_path = wav_file_path

                # # 메시지를 보낸 후 1초 대기
                # message = await ctx.send(f"목소리 종류: {voice_type}, 텍스트: {input_text}")

                # 음성 재생
                await self.play_audio(ctx, wav_file_path)
                # await ctx.send("재생이 완료되었습니다. 음성 채널에 남아 있습니다.")

                # 초기화 과정
                await self.reset_tts(ctx, wav_file_path)

                # await asyncio.sleep(5)  # 5초 대기
                # await message.delete()  # 메시지 삭제
            else:
                await ctx.send("먼저 음성 채널에 들어가 주세요.")

        except Exception as e:
            error_message = str(e)
            print(f"오류 발생: {error_message}")
            raise  # 오류를 다시 발생시켜서 process_queue에서 처리하도록 함

        finally:
            # 재생이 끝난 후 상태 초기화
            self.is_playing = False

    async def analyze_user_input(self, user_input: str):
        """사용자 입력을 분석하여 음성 유형과 입력 텍스트를 반환하는 메서드"""
        split_input = user_input.split(' ', 1)

        if len(split_input) == 2:
            front_input, back_input = split_input

            # 음성 유형 매칭
            matching_voice = next((voice for voice in self.voice_types if front_input.startswith(voice[:2])), None)
            if matching_voice:
                voice_type = matching_voice
                input_text = back_input
                self.current_voice = voice_type
            elif front_input == "랜덤":
                voice_type = random.choice(self.voice_types)  # 랜덤 음성을 선택
                input_text = back_input
                self.current_voice = "랜덤"
            else:
                voice_type = self.current_voice if self.current_voice != "랜덤" else random.choice(self.voice_types)
                input_text = user_input
        else:
            voice_type = self.current_voice if self.current_voice != "랜덤" else random.choice(self.voice_types)
            input_text = user_input if len(split_input) > 1 else split_input[0]

        return voice_type, input_text

    async def modify_text(self, replacement_text):
        """텍스트를 수정하는 메서드.""" 
        welcome_text_element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "has-focus"))
        )
        self.driver.execute_script("arguments[0].innerText = arguments[1];", welcome_text_element, replacement_text)
        await asyncio.sleep(0.5)  # 잠시 대기

    async def handle_add_request(self, ctx, add_input):
        """'tts add' 요청을 처리하는 메서드"""
        # 버튼 클릭
        await self.click_element((By.XPATH, 
        "//span[contains(@class, 'add-actor-button')]"))

        # 텍스트 입력하여 검색
        await self.input_search_text(add_input)

        # 검색 아이콘 클릭
        await self.click_element((By.XPATH, 
        "//div[contains(@class, 'search-icon')]"))
        
        await asyncio.sleep(0.5)  # 잠시 대기

        # 첫 번째 목소리 선택
        actor_selection_result = await self.select_actor_by_name(ctx, add_input)
        
        if actor_selection_result == "not_found":
            await ctx.send(f"'{add_input}'을/를 찾을 수 없습니다.")  # 찾지 못한 경우 메시지 출력
            self.driver.back()
            return  # 메서드 종료
        elif actor_selection_result == "already_added":
            await ctx.send(f"'{add_input}'은/는 이미 추가되었습니다.")  # 이미 추가된 경우 메시지 출력
            return  # 메서드 종료
        
        # 프로젝트에 추가 버튼 클릭
        await self.click_element((By.XPATH, 
        "//button[span[contains(text(), '프로젝트에 추가')]]"))

        # 음성 유형 가져오기
        await self.get_voice_types(ctx)  # 여기에 추가

        # add_input을 출력
        await ctx.send(f"'{add_input}'이/가 추가되었습니다.")  # ctx.send로 add_input 출력

    async def input_search_text(self, user_input: str):
        """검색 입력 필드에 텍스트를 입력하는 메서드."""
        try:
            search_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            search_input.clear()  # 기존 텍스트 삭제
            search_input.send_keys(user_input)  # 사용자 입력 텍스트 전송
            await asyncio.sleep(1)  # 잠시 대기
        except Exception as e:
            print(f"검색 입력 필드에 텍스트 입력 중 오류 발생: {e}")

    async def select_actor_by_name(self, ctx, actor_name):
        """주어진 이름을 가진 배우 요소를 선택하는 메서드."""
        # 모든 배우 카드 요소를 가져옴
        actor_cards = self.driver.find_elements(By.CLASS_NAME, "actor-card-wrapper")

        for card in actor_cards:
            # 이름 요소 찾기
            name_element = card.find_element(By.CLASS_NAME, "card-name")
            if actor_name in name_element.text:  # 이름이 add_input에 포함되는지 확인
                if "already-added" in card.get_attribute("class"):
                    return "already_added"  # 찾았지만 추가할 수 없음
                
                # 클릭 가능할 경우 클릭
                await self.click_element((By.XPATH, f".//div[contains(@class, 'actor-card-wrapper')][.//strong[contains(text(), '{actor_name}')]]"))
                return True  # 클릭 성공

        return "not_found"  # 찾지 못한 경우

    async def find_wav_file(self, ctx):
        """WAV 파일을 찾는 메서드.""" 
        # await ctx.send("TTS 파일 생성 중입니다...")
        media_count = 0
        retry_count = 0
        max_retries = 100
        wav_url = None

        while media_count < 1 and retry_count < max_retries:
            current_requests = self.driver.execute_script("return performance.getEntriesByType('resource');")
            for request in current_requests:
                if 'normal.wav' in request['name']:
                    media_count += 1
                    wav_url = request['name']
                    break
            await asyncio.sleep(0.2)
            retry_count += 1
        
        if media_count < 1:
            # await ctx.send("새로운 .wav 파일을 찾지 못했습니다.")
            return None

        return wav_url

    async def download_wav_file(self, ctx, wav_url):
        """WAV 파일을 다운로드하는 메서드.""" 
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            wav_file_path = tmp_file.name

        response = requests.get(wav_url)
        if response.status_code == 200:
            with open(wav_file_path, "wb") as file:
                file.write(response.content)
            return wav_file_path
        else:
            # await ctx.send("WAV 파일 다운로드에 실패했습니다.")
            return None

    async def play_audio(self, ctx, wav_file_path):
        """음성을 재생하는 메서드.""" 
        volume = 0.2  # 볼륨을 0.2로 설정
        source = discord.FFmpegPCMAudio(
            executable="C:\\File\\DiscordBot\\cogs\\TTS\\ffmpeg\\bin\\ffmpeg.exe",
            source=wav_file_path,
            options=f"-filter:a 'volume={volume}'"
        )
        
        # play() 메서드에 source만 전달
        ctx.voice_client.play(source)

        # 음성이 끝날 때까지 대기
        while ctx.voice_client.is_playing():
            await asyncio.sleep(0.1)

    async def click_floating_menu(self):
        """플로팅 메뉴 항목 클릭하는 메서드.""" 
        # 플로팅 메뉴 항목 찾기 및 클릭
        floating_menus = WebDriverWait(self.driver, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "candidate-select"))
        )
        floating_menus[4].click()  # 특정 위치 요소 클릭

    async def reset_tts(self, ctx, wav_file_path):
        """TTS 초기화 메서드.""" 
        
        # 닫기 버튼 클릭
        await self.click_element((By.XPATH, 
        "//button[span[contains(text(), '닫기')]]"))
        
        # 플로팅 메뉴 클릭
        await self.click_floating_menu()  

# Cog setup 함수
async def setup(bot):
    await bot.add_cog(TTS(bot))