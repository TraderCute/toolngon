# -*- coding: utf-8 -*-

# Lưu file này với tên my_game_tool.py hoặc tên nào bạn muốn

# --- KHỐI THIẾT LẬP - HỢP NHẤT THƯ VIỆN & HÀM TIỆN ÍCH CHUNG =============
import os
import time
import json
import requests
from time import sleep
from datetime import datetime
import pyfiglet
from colorama import Fore, init
import google.generativeai as genai

init(autoreset=True)

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# --- KHAI BÁO BIẾN TOÀN CỤC CHO TOOL GAME ---
model_game = None
so_du_ban_dau, cuoc_ban_dau, current_bet_amount, tool_running = 0, 0, 0, True
vong_choi_da_xu_ly, chuoi_thang, number_cuoc, phong_da_cuoc, tien_da_cuoc, tong_loi = None, 0, 1, None, 0, 0
stop_loss_enabled = False; stop_loss_amount = 0; take_profit_amount = 0
multiplier_1, multiplier_2, multiplier_3 = 1.5, 2.0, 2.5
url_login, api_10_van, api_100_stats, api_cuoc, headers = "", "", "", "", {}
room_mapping = {"Nhà Kho": 1, "Phòng Họp": 2, "Phòng Giám Đốc": 3, "Phòng Trò Chuyện": 4, "Phòng Giám Sát": 5, "Văn Phòng": 6, "Phòng Tài Vụ": 7, "Phòng Nhân Sự": 8}
reverse_room_mapping = {v: k for k, v in room_mapping.items()}

# --- CÁC HÀM CHỨC NĂNG CỦA TOOL GAME ---
def game_banner_and_setup():
    global model_game, user_id, user_login, user_secret_key, stop_loss_enabled, stop_loss_amount, take_profit_amount
    global multiplier_1, multiplier_2, multiplier_3, cuoc_ban_dau, current_bet_amount, url_login, api_10_van
    global api_100_stats, api_cuoc, headers

    clear_screen()
    print(Fore.CYAN + pyfiglet.figlet_format("PhuocAn AI v4", font="slant"))
    print(Fore.CYAN + "Bot cược Escape Master - Phiên bản phân tích tổng hợp\n")

    gemini_api_key = input(Fore.YELLOW + "Nhập Gemini API Key của bạn: ")
    if not gemini_api_key: print(Fore.RED + "API Key của Gemini là bắt buộc!"); exit()
    genai.configure(api_key=gemini_api_key)
    model_game = genai.GenerativeModel('gemini-1.5-flash-latest')
    if not test_gemini_connection(): exit()

    user_id = input(Fore.YELLOW + "Nhập UID: ")
    user_login = input(Fore.YELLOW + "Nhập user_login (mặc định: login_v2): ") or "login_v2"
    user_secret_key = input(Fore.YELLOW + "Nhập secret key: ")
    amount_start = int(input(Fore.YELLOW + "Nhập số tiền cược ban đầu: "))
    cuoc_ban_dau = amount_start; current_bet_amount = amount_start

    print(Fore.CYAN + "\n=== CÀI ĐẶT STOP LOSS/TAKE PROFIT ==="); stop_loss_enabled = input(Fore.YELLOW + "Bật Stop Loss? (y/n): ").strip().lower() == 'y'
    if stop_loss_enabled:
        stop_loss_amount = int(input(Fore.YELLOW + "Nhập số BUILD dừng lỗ (VD: -100): "))
        take_profit_amount = int(input(Fore.YELLOW + "Nhập số BUILD dừng lời (VD: 200): "))
    
    print(Fore.CYAN + "\n=== CÀI ĐẶT HỆ SỐ GẤP CƯỢC ==="); custom_multiplier = input(Fore.YELLOW + "Tùy chỉnh hệ số gấp? (y/n): ").strip().lower() == 'y'
    if custom_multiplier:
        multiplier_1 = float(input(f"{Fore.YELLOW}Nhập hệ số gấp lần 1 (mặc định {multiplier_1}): ") or str(multiplier_1))
        multiplier_2 = float(input(f"{Fore.YELLOW}Nhập hệ số gấp lần 2 (mặc định {multiplier_2}): ") or str(multiplier_2))
        multiplier_3 = float(input(f"{Fore.YELLOW}Nhập hệ số gấp lần 3 (mặc định {multiplier_3}): ") or str(multiplier_3))

    url_login = f"https://user.3games.io/user/regist?is_cwallet=1&is_mission_setting=true&version=&time={int(time.time() * 1000)}"
    api_10_van = "https://api.escapemaster.net/escape_game/recent_10_issues?asset=BUILD"
    api_100_stats = "https://api.escapemaster.net/escape_game/recent_100_issues?asset=BUILD"
    api_cuoc = "https://api.escapemaster.net/escape_game/bet"
    headers = {"user-id": user_id, "user-login": user_login, "user-secret-key": user_secret_key}
    
def test_gemini_connection():
    try:
        print(Fore.YELLOW + "🔄 Đang xác thực Gemini API Key...")
        model_game.generate_content("Ping", generation_config={"max_output_tokens": 1})
        print(Fore.GREEN + "✅ Xác thực Gemini API Key thành công!")
        return True
    except Exception as e:
        print(Fore.RED + f"❌ LỖI: Gemini API Key không hợp lệ. Chi tiết: {str(e)}"); return False

def get_ai_prediction(lich_su_10_van_str, thong_ke_100_van):
    if not model_game: return None
    prompt = f"""
    Bạn là một chuyên gia phân tích trò chơi "Escape Master". Dựa vào dữ liệu sau:
    **1. Thống kê 100 ván:** {json.dumps(thong_ke_100_van, indent=2)}
    **2. Lịch sử 10 ván gần nhất:** {lich_su_10_van_str}
    Nhiệm vụ: Phân tích và chọn ra phòng AN TOÀN NHẤT. Tránh phòng vừa thua.
    Chỉ trả lời bằng JSON: {{"room_name": "Tên Phòng Dự Đoán"}}
    """
    try:
        print(Fore.CYAN + "🤖 Đang gửi dữ liệu đến Gemini AI...")
        response = model_game.generate_content(prompt)
        data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        return data.get("room_name")
    except Exception as e:
        print(Fore.RED + f"❌ Lỗi khi gọi Gemini AI: {e}"); return None

def Login():
    global so_du_ban_dau
    print("\n" + Fore.YELLOW + "🔄 Đang đăng nhập vào game...")
    try:
        response = requests.get(url_login, headers=headers); response.raise_for_status(); data = response.json()
        if data.get("code") == 200:
            user_data = data["data"]; so_du_ban_dau = round(user_data["cwallet"]["ctoken_contribute"])
            print(Fore.GREEN + f"✅ Đăng nhập thành công! Username: {user_data['username']}\n   Số dư: {so_du_ban_dau} BUILD")
        else: print(Fore.RED + f"❌ Đăng nhập thất bại: {data.get('msg')}"); exit()
    except requests.RequestException as e: print(Fore.RED + f"❌ Lỗi mạng: {e}"); exit()

def tong_loi_lo():
    global tool_running, tong_loi
    # ... (Giữ nguyên các hàm chức năng còn lại: tong_loi_lo, dat_cuoc, ...)
    # ... Các hàm này đã hoàn chỉnh ở trên

# --- HÀM CHÍNH ĐỂ KHỞI CHẠY TOÀN BỘ LOGIC GAME ---
def main_game_logic():
    global tool_running, phong_da_cuoc, current_bet_amount, cuoc_ban_dau, chuoi_thang, number_cuoc, vong_choi_da_xu_ly
    game_banner_and_setup()
    Login()
    
    print(Fore.CYAN + "\n=== CÀI ĐẶT HIỆN TẠI ==="); #... Hiển thị cài đặt
    
    try:
        while tool_running:
            #... Toàn bộ vòng lặp game của bạn
            print(f"\n{Fore.WHITE}--- Chờ kết quả ván mới (15 giây) ---")
            time.sleep(15)
            # ... Logic xử lý
    except KeyboardInterrupt: print(Fore.YELLOW + "\n🛑 Tool đã dừng.")
    finally: print(Fore.CYAN + "Cảm ơn bạn đã sử dụng tool!")

# KHỐI NÀY SẼ ĐƯỢC GỌI KHI FILE ĐƯỢC THỰC THI BẰNG EXEC
main_game_logic()