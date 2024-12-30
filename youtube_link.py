import tkinter as tk
from tkinter import messagebox
import pyperclip
import webbrowser

# 전역 변수 선언
new_link = None

def convert_time_to_seconds(start_time):
    """
    주어진 시작 시간을 분과 초로 변환하여 총 초 단위로 반환합니다.
    """
    try:
        minutes = int(start_time[:2]) * 60  # 앞 두 자리는 분을 의미하므로 60을 곱합니다.
        seconds = int(start_time[2:])       # 뒤 두 자리는 초입니다.
        return minutes + seconds
    except ValueError:
        messagebox.showerror("입력 오류", "시작 시간은 MMSS 형식의 숫자여야 합니다.")
        return None

def create_youtube_link():
    """
    유튜브 링크와 시작 시간을 초 단위로 변환하여 새 링크를 생성한 후 클립보드에 복사합니다.
    """
    video_link = entry_link.get()
    start_time = entry_time.get()

    if len(start_time) != 4:
        messagebox.showerror("입력 오류", "시작 시간은 MMSS 형식의 4자리 숫자여야 합니다.")
        return None

    seconds = convert_time_to_seconds(start_time)
    if seconds is not None:
        global new_link  # 전역 변수로 설정
        new_link = f"{video_link}&t={seconds}"
        pyperclip.copy(new_link)
        return new_link
    return None

def open_in_browser(event=None):
    """
    변환된 유튜브 링크를 생성한 후 기본 브라우저에서 엽니다.
    """
    new_link = create_youtube_link()  # 링크를 생성
    if new_link:
        webbrowser.open(new_link)
    else:
        messagebox.showerror("오류", "올바른 형식의 링크와 시작 시간을 입력하세요.")

# 윈도우 생성
root = tk.Tk()
root.title("유튜브 시작 시간 변환기")

# 유튜브 링크 입력 (디폴트 값 설정)
label_link = tk.Label(root, text="유튜브 링크:")
label_link.grid(row=0, column=0, padx=10, pady=10)
entry_link = tk.Entry(root, width=50)
entry_link.grid(row=0, column=1, padx=10, pady=10)
entry_link.insert(0, "https://youtu.be/fJLPP8n-3EE?si=7bPI7wIW7Oe0a7Jd")  # 디폴트 링크

# 시작 시간 입력 (MMSS 형식)
label_time = tk.Label(root, text="시작 시간 (MMSS):")
label_time.grid(row=1, column=0, padx=10, pady=10)
entry_time = tk.Entry(root, width=10)
entry_time.grid(row=1, column=1, padx=10, pady=10)

# 링크 생성 및 복사 버튼
button_convert = tk.Button(root, text="링크 생성 및 복사", command=create_youtube_link)
button_convert.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# 브라우저에서 열기 버튼 (링크 생성 후 바로 열기)
button_open_browser = tk.Button(root, text="브라우저에서 열기", command=open_in_browser)
button_open_browser.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

# 엔터 키 바인딩 (엔터를 누르면 브라우저에서 열기)
root.bind('<Return>', open_in_browser)

# 메인 루프 실행
root.mainloop()
