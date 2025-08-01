import os
import time
import pyfiglet
import requests
import json
import re
from colorama import Fore, Style, init

# --- KHỞI TẠO CÁC BIẾN TOÀN CỤC ---
init(autoreset=True)
SETTINGS_FILE = 'settings.json' # Tên file để lưu cài đặt
tong_loi = 0
phong_da_cuoc = None
tien_da_cuoc = 0
model = None

# --- CÁC HÀM TIỆN ÍCH, LƯU/TẢI CÀI ĐẶT ---
def clear_screen(): os.system("cls" if os.name == "nt" else "clear")

def print_colored_ascii_art(text):
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
    ascii_art = pyfiglet.figlet_format(text, font="slant"); lines = ascii_art.splitlines()
    for i, line in enumerate(lines): print(colors[i % len(colors)] + line)

def save_settings(settings_data):
    """Lưu trữ dict cài đặt vào file JSON."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=4)
        print(Fore.GREEN + "✅ Cài đặt đã được lưu cho lần chạy sau.")
    except IOError as e:
        print(Fore.RED + f"❌ Không thể lưu cài đặt: {e}")

def load_settings():
    """Tải cài đặt từ file JSON nếu có."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None

def mask_key(key, show_first=4, show_last=4):
    """Che bớt key để hiển thị an toàn."""
    if not isinstance(key, str) or len(key) <= show_first + show_last:
        return "********"
    return f"{key[:show_first]}...{key[-show_last:]}"

# --- LOGIC LIÊN QUAN TỚI GEMINI AI (Không đổi) ---
def test_gemini_connection():
    try:
        print(Fore.YELLOW + "🔄 Đang xác thực Gemini API Key..."); model.generate_content("Ping", generation_config={"max_output_tokens": 1}); print(Fore.GREEN + "✅ Xác thực Gemini API Key thành công!")
        return True
    except Exception as e:
        print(Fore.RED + f"❌ LỖI: Gemini API Key không hợp lệ. Chi tiết: {str(e)}"); return False

def get_ai_prediction(lich_su_10_van_str, thong_ke_100_van):
    if not model: return None
    prompt = f"""
    Bạn là một chuyên gia phân tích dữ liệu cho trò chơi may rủi "Escape Master". Nhiệm vụ của bạn là kết hợp dữ liệu dài hạn và ngắn hạn để đưa ra dự đoán phòng an toàn nhất.
    **1. Dữ liệu dài hạn (Thống kê 100 ván gần nhất):**
    Đây là số lần mỗi phòng có "sát thủ" trong 100 ván qua. Số càng cao, phòng càng nguy hiểm.
    {json.dumps(thong_ke_100_van, indent=2, ensure_ascii=False)}
    **2. Dữ liệu ngắn hạn (Lịch sử 10 ván gần nhất):**
    Đây là diễn biến của 10 ván gần đây nhất (ván mới nhất ở đầu).
    {lich_su_10_van_str}
    **Nhiệm vụ:** Phân tích và tìm ra phòng an toàn nhất để cược, ưu tiên các phòng an toàn trong dài hạn và không xuất hiện sát thủ gần đây.
    Chỉ trả lời bằng một đối tượng JSON duy nhất theo định dạng: {{"room_name": "Tên Phòng Dự Đoán"}}"""
    try:
        print(Fore.CYAN + "🤖 Đang gửi dữ liệu tổng hợp đến Gemini AI..."); response = model.generate_content(prompt)
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if match:
            json_str = match.group(0); data = json.loads(json_str); predicted_room = data.get("room_name")
            print(Fore.GREEN + f"🧠 Gemini AI đề xuất: '{predicted_room}'"); return predicted_room
        else:
            print(Fore.RED + "❌ Không tìm thấy JSON trong phản hồi từ AI."); return None
    except Exception as e: print(Fore.RED + f"❌ Lỗi khi gọi Gemini AI: {e}"); return None

# --- CÁC HÀM LOGIC GAME (Không đổi) ---
def Login():
    global so_du_ban_dau
    print("\n" + Fore.YELLOW + "🔄 Đang đăng nhập vào game...")
    try:
        response = requests.get(url_login, headers=headers); response.raise_for_status(); data = response.json()
        if data.get("code") == 200:
            user_data = data["data"]; username = user_data["username"]; so_du_ban_dau = round(user_data["cwallet"]["ctoken_contribute"])
            print(Fore.GREEN + f"✅ Đăng nhập thành công! Username: {username}\n   Số dư ban đầu: {so_du_ban_dau} BUILD")
        else: print(Fore.RED + f"❌ Đăng nhập thất bại: {data.get('msg', 'Lỗi không xác định')}"); exit()
    except requests.RequestException as e: print(Fore.RED + f"❌ Lỗi mạng khi đăng nhập: {e}"); exit()

def tong_loi_lo():
    global tool_running, tong_loi
    try:
        response = requests.get(url_login, headers=headers); response.raise_for_status(); data = response.json()
        if data.get("code") == 200:
            current_balance = round(data["data"]["cwallet"]["ctoken_contribute"]); tong_loi = current_balance - so_du_ban_dau
            color = Fore.GREEN if tong_loi >= 0 else Fore.RED
            print(Fore.LIGHTWHITE_EX + f"📈 Số dư: {current_balance} BUILD | Lời/Lỗ: {color}{tong_loi} BUILD")
            if stop_loss_enabled and ((tong_loi <= -stop_loss_amount) or (tong_loi >= take_profit_amount)):
                print(Fore.RED + "🛑 ĐIỀU KIỆN DỪNG TOOL ĐÃ ĐẠT!"); tool_running = False
    except requests.RequestException: print(Fore.YELLOW + "⚠️ Lỗi mạng khi kiểm tra số dư.")

def dat_cuoc(room_id, bet_amount):
    global phong_da_cuoc, tien_da_cuoc
    body = {"asset_type": "BUILD", "bet_amount": int(bet_amount), "room_id": room_id}
    try:
        response = requests.post(api_cuoc, headers=headers, json=body); data = response.json()
        if response.status_code == 200 and data.get("code") == 0:
            room_name = reverse_room_mapping.get(room_id, "?"); print(Fore.BLUE + f"🎯 Cược {int(bet_amount)} BUILD vào '{room_name}'")
            phong_da_cuoc = room_id; tien_da_cuoc = int(bet_amount); return True
        else:
            print(Fore.RED + f"❌ Lỗi cược: {data.get('msg', 'Lỗi không xác định')}"); phong_da_cuoc = None; return False
    except requests.RequestException as e: print(Fore.RED + f"❌ Lỗi mạng khi cược: {e}"); phong_da_cuoc = None; return False


# ================== MAIN SCRIPT START ==================
if __name__ == "__main__":
    clear_screen()
    print_colored_ascii_art("PHUOCAN AI v6")
    print(Fore.CYAN + "Bot cược Escape Master - Phiên bản có lưu cài đặt\n")

    # --- KHỐI LOGIC MỚI: TẢI HOẶC YÊU CẦU CÀI ĐẶT ---
    settings = load_settings()
    use_saved_settings = False
    if settings:
        print(Fore.GREEN + "Đã tìm thấy cài đặt đã lưu:")
        print(f"  - Gemini API Key: {Fore.YELLOW}{mask_key(settings.get('gemini_api_key'))}")
        print(f"  - UID:            {Fore.YELLOW}{settings.get('uid')}")
        print(f"  - Secret Key:     {Fore.YELLOW}{mask_key(settings.get('secret_key'))}")
        
        while True:
            choice = input(Fore.CYAN + "Bạn có muốn sử dụng cài đặt này không? (y/n): ").strip().lower()
            if choice in ['y', 'n']:
                use_saved_settings = (choice == 'y')
                break
            else:
                print(Fore.RED + "Vui lòng chỉ nhập 'y' hoặc 'n'.")
    
    if not use_saved_settings:
        if settings:
             print("\n" + Fore.YELLOW + "Vui lòng nhập lại cài đặt mới.")
        else:
             print(Fore.YELLOW + "Không tìm thấy file cài đặt. Vui lòng nhập lần đầu.")
        settings = {
            'gemini_api_key': input(Fore.YELLOW + "Nhập Gemini API Key của bạn: "),
            'uid': input(Fore.YELLOW + "Nhập UID: "),
            'user_login': input(Fore.YELLOW + "Nhập user_login (mặc định: login_v2): ") or "login_v2",
            'secret_key': input(Fore.YELLOW + "Nhập secret key: ")
        }
        save_settings(settings)
    
    # Gán các biến từ dict 'settings'
    GEMINI_API_KEY = settings['gemini_api_key']
    user_id = settings['uid']
    user_login = settings['user_login']
    user_secret_key = settings['secret_key']

    try: import google.generativeai as genai
    except ImportError: print(Fore.RED + "Lỗi: 'pip install google-generativeai'"); exit()
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    if not test_gemini_connection(): exit()

    # --- TIẾP TỤC VỚI CÁC CÀI ĐẶT TRONG GAME ---
    amount = int(input(Fore.YELLOW + "Nhập số tiền cược ban đầu: "))
    print(Fore.CYAN + "\n=== CÀI ĐẶT STOP LOSS/TAKE PROFIT ==="); stop_loss_enabled = input(Fore.YELLOW + "Bật Stop Loss? (y/n): ").strip().lower() == 'y'
    stop_loss_amount, take_profit_amount = 0, 0
    if stop_loss_enabled: stop_loss_amount = int(input(Fore.YELLOW + "Nhập số BUILD dừng lỗ: ")); take_profit_amount = int(input(Fore.YELLOW + "Nhập số BUILD dừng lời: "))
    print(Fore.CYAN + "\n=== CÀI ĐẶT HỆ SỐ GẤP CƯỢC ==="); custom_multiplier = input(Fore.YELLOW + "Tùy chỉnh hệ số gấp? (y/n): ").strip().lower() == 'y'
    multiplier_1, multiplier_2, multiplier_3 = 1.5, 2.0, 2.5
    if custom_multiplier:
        multiplier_1 = float(input(f"{Fore.YELLOW}Gấp lần 1 (mặc định {multiplier_1}): ") or str(multiplier_1))
        multiplier_2 = float(input(f"{Fore.YELLOW}Gấp lần 2 (mặc định {multiplier_2}): ") or str(multiplier_2))
        multiplier_3 = float(input(f"{Fore.YELLOW}Gấp lần 3 (mặc định {multiplier_3}): ") or str(multiplier_3))
    
    # --- KHỞI TẠO BIẾN, API, HEADER VÀ CHẠY VÒNG LẶP CHÍNH ---
    cuoc_ban_dau, current_bet_amount, so_du_ban_dau, tool_running = amount, amount, 0, True
    vong_choi_da_xu_ly, chuoi_thang, number_cuoc = None, 0, 1
    
    url_login = f"https://user.3games.io/user/regist?is_cwallet=1&is_mission_setting=true&version=&time={int(time.time() * 1000)}"
    api_10_van = "https://api.escapemaster.net/escape_game/recent_10_issues?asset=BUILD"
    api_100_stats = "https://api.escapemaster.net/escape_game/recent_100_issues?asset=BUILD"
    api_cuoc = "https://api.escapemaster.net/escape_game/bet"
    headers = {"user-id": user_id, "user-login": user_login, "user-secret-key": user_secret_key}
    room_mapping = {"Nhà Kho": 1, "Phòng Họp": 2, "Phòng Giám Đốc": 3, "Phòng Trò Chuyện": 4, "Phòng Giám Sát": 5, "Văn Phòng": 6, "Phòng Tài Vụ": 7, "Phòng Nhân Sự": 8}
    reverse_room_mapping = {v: k for k, v in room_mapping.items()}

    Login()
    print(Fore.CYAN + "\n=== CÀI ĐẶT HOÀN TẤT ==="); print("="*50)
    
    try:
        # (Phần vòng lặp chính giữ nguyên như v5)
        while tool_running:
            print(f"\n{Fore.WHITE}--- Chờ kết quả ván mới (15 giây) ---"); time.sleep(15)
            try:
                res_10 = requests.get(api_10_van, headers=headers); res_10.raise_for_status(); data_10 = res_10.json()
                if not (data_10.get("code") == 0 and data_10.get("data")): print(Fore.RED + "❌ Lỗi: API 10 ván."); continue
                lich_su_chi_tiet = data_10["data"]
                res_100 = requests.get(api_100_stats, headers=headers); res_100.raise_for_status(); data_100 = res_100.json()
                if not (data_100.get("code") == 0 and data_100.get("data")): print(Fore.RED + "❌ Lỗi: API 100 ván."); continue
                thong_ke_thua = data_100["data"]["room_id_2_killed_times"]
            except requests.RequestException as e: print(Fore.RED + f"Lỗi mạng khi lấy dữ liệu: {e}"); continue
            
            latest_issue = lich_su_chi_tiet[0]; vong_choi_moi = latest_issue["issue_id"]
            if vong_choi_moi == vong_choi_da_xu_ly: print(Fore.YELLOW + "Chưa có ván mới..."); continue
            id_ket_qua_vong_truoc = latest_issue["killed_room_id"]; ten_phong_vong_truoc = reverse_room_mapping.get(id_ket_qua_vong_truoc, "?")
            print(Fore.LIGHTCYAN_EX + f"\nVòng #{vong_choi_moi} đã kết thúc. Sát thủ ở: {ten_phong_vong_truoc}"); vong_choi_da_xu_ly = vong_choi_moi
            if phong_da_cuoc is not None:
                thang = (phong_da_cuoc != id_ket_qua_vong_truoc)
                if thang:
                    print(Fore.GREEN + f"✅ THẮNG! (+{tien_da_cuoc} BUILD)"); chuoi_thang += 1; current_bet_amount = cuoc_ban_dau; number_cuoc = 1
                else:
                    print(Fore.RED + f"❌ THUA! (-{tien_da_cuoc} BUILD)"); chuoi_thang = 0
                    if number_cuoc == 1: current_bet_amount *= multiplier_1; number_cuoc = 2
                    elif number_cuoc == 2: current_bet_amount *= multiplier_2; number_cuoc = 3
                    elif number_cuoc == 3: current_bet_amount *= multiplier_3; number_cuoc = 4
                    else: current_bet_amount = cuoc_ban_dau; number_cuoc = 1; print(Fore.RED + "🚫 Reset cược.")
                tong_loi_lo()
                if not tool_running: break
            
            lich_su_str = "\n".join([f"#{d['issue_id']}: {reverse_room_mapping.get(d['killed_room_id'],'N/A')}" for d in lich_su_chi_tiet])
            thong_ke_doc = {reverse_room_mapping.get(int(k), k): v for k, v in thong_ke_thua.items()}
            predicted_room_name = get_ai_prediction(lich_su_str, thong_ke_doc)
            if predicted_room_name in room_mapping: dat_cuoc(room_mapping[predicted_room_name], current_bet_amount)
            else: print(Fore.RED + "AI không dự đoán được. Bỏ qua."); phong_da_cuoc = None
    except KeyboardInterrupt: print(Fore.YELLOW + "\n🛑 Đã dừng bởi người dùng.")
    finally: print(Fore.CYAN + "Cảm ơn đã sử dụng tool!")
