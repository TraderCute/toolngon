import os
import time
import pyfiglet
import requests
import json
import re  # <<< THÊM THƯ VIỆN REGEX ĐỂ XỬ LÝ JSON
from colorama import Fore, Style, init

# --- KHỞI TẠO CÁC BIẾN TOÀN CỤC ---
init(autoreset=True)
tong_loi = 0
phong_da_cuoc = None
tien_da_cuoc = 0
model = None

# --- CÁC HÀM TIỆN ÍCH VÀ AI ---
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_colored_ascii_art(text):
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
    ascii_art = pyfiglet.figlet_format(text, font="slant")
    lines = ascii_art.splitlines()
    for i, line in enumerate(lines):
        print(colors[i % len(colors)] + line)

def test_gemini_connection():
    try:
        print(Fore.YELLOW + "🔄 Đang xác thực Gemini API Key...")
        model.generate_content("Ping", generation_config={"max_output_tokens": 1})
        print(Fore.GREEN + "✅ Xác thực Gemini API Key thành công!")
        return True
    except Exception as e:
        print(Fore.RED + f"❌ LỖI: Gemini API Key không hợp lệ. Chi tiết: {str(e)}")
        return False

def get_ai_prediction(lich_su_10_van_str, thong_ke_100_van):
    if not model: return None

    prompt = f"""
    Bạn là một chuyên gia phân tích dữ liệu cho trò chơi may rủi "Escape Master". Nhiệm vụ của bạn là kết hợp dữ liệu dài hạn và ngắn hạn để đưa ra dự đoán phòng an toàn nhất.

    **1. Dữ liệu dài hạn (Thống kê 100 ván gần nhất):**
    Đây là số lần mỗi phòng có "sát thủ" trong 100 ván qua. Số càng cao, phòng càng nguy hiểm về mặt thống kê.
    {json.dumps(thong_ke_100_van, indent=2, ensure_ascii=False)}

    **2. Dữ liệu ngắn hạn (Lịch sử 10 ván gần nhất):**
    Đây là diễn biến của 10 ván gần đây nhất (ván mới nhất ở đầu).
    {lich_su_10_van_str}

    **Nhiệm vụ của bạn:**
    1.  Dựa vào dữ liệu dài hạn, xác định các phòng "an toàn" (ít bị sát thủ vào nhất).
    2.  Dựa vào dữ liệu ngắn hạn, loại trừ phòng vừa có sát thủ ở ván gần nhất.
    3.  Cân nhắc cả hai yếu tố trên để đưa ra một lựa chọn duy nhất cho phòng bạn tin là **AN TOÀN NHẤT**.

    Chỉ trả lời bằng một đối tượng JSON duy nhất theo định dạng: {{"room_name": "Tên Phòng Dự Đoán"}}
    """

    try:
        print(Fore.CYAN + "🤖 Đang gửi dữ liệu tổng hợp (100 ván + 10 ván) đến Gemini AI...")
        response = model.generate_content(prompt)
        ai_response_text = response.text

        # === PHẦN SỬA LỖI JSON QUAN TRỌNG NHẤT ===
        # Dùng regex để tìm chuỗi bắt đầu bằng { và kết thúc bằng }, bất kể các dòng và ký tự thừa
        match = re.search(r"\{.*\}", ai_response_text, re.DOTALL)

        if match:
            json_str = match.group(0)
            data = json.loads(json_str)  # Thử phân tích chuỗi JSON đã được trích xuất
            predicted_room = data.get("room_name")
            print(Fore.GREEN + f"🧠 Gemini AI (phân tích tổng hợp) đề xuất: '{predicted_room}'")
            return predicted_room
        else:
            print(Fore.RED + "❌ Không tìm thấy đối tượng JSON hợp lệ trong phản hồi từ AI.")
            print(Fore.YELLOW + f"   Phản hồi thô từ AI: {ai_response_text}")
            return None

    except json.JSONDecodeError as json_err:
        print(Fore.RED + f"❌ Lỗi phân tích JSON từ phản hồi của AI: {json_err}")
        print(Fore.YELLOW + f"   Phản hồi thô từ AI: {ai_response_text}")
        return None
    except Exception as e:
        print(Fore.RED + f"❌ Lỗi không xác định khi gọi Gemini AI: {e}")
        return None

# --- THU THẬP THÔNG TIN VÀ CÀI ĐẶT ---
clear_screen()
print_colored_ascii_art("TraderDz")
print(Fore.CYAN + "Bot cược Escape Master - Bú đẫm\n")
try:
    import google.generativeai as genai
except ImportError: print(Fore.RED + "Lỗi: Vui lòng cài đặt thư viện 'pip install google-generativeai'"); exit()

GEMINI_API_KEY = input(Fore.YELLOW + "Nhập Gemini API Key của bạn: ")
if not GEMINI_API_KEY: print(Fore.RED + "API Key của Gemini là bắt buộc!"); exit()
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')
if not test_gemini_connection(): exit()

user_id = input(Fore.YELLOW + "Nhập UID: ")
user_login = input(Fore.YELLOW + "Nhập user_login (mặc định: login_v2): ") or "login_v2"
user_secret_key = input(Fore.YELLOW + "Nhập secret key: ")
amount = int(input(Fore.YELLOW + "Nhập số tiền cược ban đầu (nhỏ nhất 1 build): "))

# Cài đặt SL/TP và hệ số gấp
print(Fore.CYAN + "\n=== CÀI ĐẶT STOP LOSS/TAKE PROFIT ==="); stop_loss_enabled = input(Fore.YELLOW + "Bật Stop Loss? (y/n): ").strip().lower() == 'y'
stop_loss_amount, take_profit_amount = 0, 0
if stop_loss_enabled: stop_loss_amount = int(input(Fore.YELLOW + "Nhập số BUILD dừng lỗ: ")); take_profit_amount = int(input(Fore.YELLOW + "Nhập số BUILD dừng lời: "))
print(Fore.CYAN + "\n=== CÀI ĐẶT HỆ SỐ GẤP CƯỢC ==="); custom_multiplier = input(Fore.YELLOW + "Tùy chỉnh hệ số gấp? (y/n): ").strip().lower() == 'y'
multiplier_1, multiplier_2, multiplier_3 = 1.5, 2.0, 2.5
if custom_multiplier:
    multiplier_1 = float(input(f"{Fore.YELLOW}Nhập hệ số gấp lần 1 (mặc định {multiplier_1}): ") or str(multiplier_1))
    multiplier_2 = float(input(f"{Fore.YELLOW}Nhập hệ số gấp lần 2 (mặc định {multiplier_2}): ") or str(multiplier_2))
    multiplier_3 = float(input(f"{Fore.YELLOW}Nhập hệ số gấp lần 3 (mặc định {multiplier_3}): ") or str(multiplier_3))

# --- KHỞI TẠO CÁC BIẾN TRẠNG THÁI VÀ API ---
cuoc_ban_dau, current_bet_amount, so_du_ban_dau, tool_running = amount, amount, 0, True
vong_choi_da_xu_ly, chuoi_thang, number_cuoc = None, 0, 1

url_login = f"https://user.3games.io/user/regist?is_cwallet=1&is_mission_setting=true&version=&time={int(time.time() * 1000)}"
api_10_van = "https://api.escapemaster.net/escape_game/recent_10_issues?asset=BUILD"
api_100_stats = "https://api.escapemaster.net/escape_game/recent_100_issues?asset=BUILD"
api_cuoc = "https://api.escapemaster.net/escape_game/bet"
headers = {"user-id": user_id, "user-login": user_login, "user-secret-key": user_secret_key}
room_mapping = {"Nhà Kho": 1, "Phòng Họp": 2, "Phòng Giám Đốc": 3, "Phòng Trò Chuyện": 4, "Phòng Giám Sát": 5, "Văn Phòng": 6, "Phòng Tài Vụ": 7, "Phòng Nhân Sự": 8}
reverse_room_mapping = {v: k for k, v in room_mapping.items()}

# --- CÁC HÀM LOGIC CHÍNH CỦA GAME (Không thay đổi so với v4) ---
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
            print(Fore.LIGHTWHITE_EX + f"📈 Số dư hiện tại: {current_balance} BUILD | Lời/Lỗ: {color}{tong_loi} BUILD")
            if stop_loss_enabled and ((tong_loi <= -stop_loss_amount) or (tong_loi >= take_profit_amount)):
                print(Fore.RED + "🛑 ĐIỀU KIỆN DỪNG TOOL ĐÃ ĐẠT!"); tool_running = False
    except requests.RequestException: print(Fore.YELLOW + "⚠️ Không thể lấy số dư hiện tại do lỗi mạng.")

def dat_cuoc(room_id, bet_amount):
    global phong_da_cuoc, tien_da_cuoc
    body = {"asset_type": "BUILD", "bet_amount": int(bet_amount), "room_id": room_id}
    try:
        response = requests.post(api_cuoc, headers=headers, json=body); data = response.json()
        if response.status_code == 200 and data.get("code") == 0:
            room_name = reverse_room_mapping.get(room_id, "?"); print(Fore.BLUE + f"🎯 Đặt cược thành công {int(bet_amount)} BUILD vào phòng '{room_name}'")
            phong_da_cuoc = room_id; tien_da_cuoc = int(bet_amount); return True
        else:
            print(Fore.RED + f"❌ Lỗi cược: {data.get('msg', 'Lỗi không xác định')}"); phong_da_cuoc = None; return False
    except requests.RequestException as e:
        print(Fore.RED + f"❌ Lỗi mạng khi đặt cược: {e}"); phong_da_cuoc = None; return False

# --- VÒNG LẶP CHÍNH CỦA BOT (Không thay đổi so với v4) ---
if __name__ == "__main__":
    Login()
    print(Fore.CYAN + "\n=== CÀI ĐẶT HIỆN TẠI ==="); print(f"Tiền cược ban đầu: {cuoc_ban_dau} BUILD")
    if stop_loss_enabled: print(f"Stop Loss: -{stop_loss_amount} BUILD | Take Profit: +{take_profit_amount} BUILD")
    else: print("Stop Loss/Take Profit: TẮT")
    print(f"Hệ số gấp: x{multiplier_1} | x{multiplier_2} | x{multiplier_3}"); print("="*50)
    try:
        while tool_running:
            print(f"\n{Fore.WHITE}--- Chờ kết quả ván mới (15 giây) ---"); time.sleep(15)
            try:
                res_10 = requests.get(api_10_van, headers=headers); res_10.raise_for_status(); data_10 = res_10.json()
                if not (data_10.get("code") == 0 and isinstance(data_10.get("data"), list) and data_10["data"]):
                    print(Fore.RED + "❌ Lỗi: Dữ liệu API 10 ván không hợp lệ."); continue
                lich_su_chi_tiet = data_10["data"]
                res_100 = requests.get(api_100_stats, headers=headers); res_100.raise_for_status(); data_100 = res_100.json()
                if not (data_100.get("code") == 0 and isinstance(data_100.get("data"), dict)):
                    print(Fore.RED + "❌ Lỗi: Dữ liệu API 100 ván không hợp lệ."); continue
                thong_ke_thua = data_100["data"]["room_id_2_killed_times"]
            except requests.RequestException as e: print(Fore.RED + f"Lỗi mạng khi lấy dữ liệu game: {e}"); continue
            
            latest_issue = lich_su_chi_tiet[0]; vong_choi_moi = latest_issue["issue_id"]
            if vong_choi_moi == vong_choi_da_xu_ly: print(Fore.YELLOW + "Chưa có ván mới, đang chờ..."); continue
            id_ket_qua_vong_truoc = latest_issue["killed_room_id"]
            ten_phong_vong_truoc = reverse_room_mapping.get(id_ket_qua_vong_truoc, "?")
            print(Fore.LIGHTCYAN_EX + f"\nVòng #{vong_choi_moi} đã kết thúc. Sát thủ ở: {ten_phong_vong_truoc}"); vong_choi_da_xu_ly = vong_choi_moi
            if phong_da_cuoc is not None:
                thang = (phong_da_cuoc != id_ket_qua_vong_truoc)
                if thang:
                    print(Fore.GREEN + f"✅ THẮNG! (+{tien_da_cuoc} BUILD)"); chuoi_thang += 1; current_bet_amount = cuoc_ban_dau; number_cuoc = 1
                    print(Fore.LIGHTMAGENTA_EX + f"🔥 Chuỗi thắng: {chuoi_thang} ván. Reset tiền cược.")
                else:
                    print(Fore.RED + f"❌ THUA! (-{tien_da_cuoc} BUILD)"); chuoi_thang = 0
                    if number_cuoc == 1: current_bet_amount *= multiplier_1; number_cuoc = 2; print(Fore.YELLOW + f"💰 Gấp cược x{multiplier_1}: {int(current_bet_amount)} BUILD")
                    elif number_cuoc == 2: current_bet_amount *= multiplier_2; number_cuoc = 3; print(Fore.YELLOW + f"💰 Gấp cược x{multiplier_2}: {int(current_bet_amount)} BUILD")
                    elif number_cuoc == 3: current_bet_amount *= multiplier_3; number_cuoc = 4; print(Fore.YELLOW + f"💰 Gấp cược x{multiplier_3}: {int(current_bet_amount)} BUILD")
                    else: current_bet_amount = cuoc_ban_dau; number_cuoc = 1; print(Fore.RED + "🚫 Đã đạt gấp cược tối đa! Reset cược.")
                tong_loi_lo()
                if not tool_running: break
            
            lich_su_str_cho_ai = "\n".join([f"Ván #{d['issue_id']}: Sát thủ ở {reverse_room_mapping.get(d['killed_room_id'], 'N/A')}" for d in lich_su_chi_tiet])
            thong_ke_de_doc = {reverse_room_mapping.get(int(k), k): v for k, v in thong_ke_thua.items()}
            predicted_room_name = get_ai_prediction(lich_su_str_cho_ai, thong_ke_de_doc)
            if predicted_room_name and predicted_room_name in room_mapping:
                dat_cuoc(room_mapping[predicted_room_name], current_bet_amount)
            else: print(Fore.RED + "AI không đưa ra dự đoán hợp lệ. Bỏ qua ván này."); phong_da_cuoc = None
    except KeyboardInterrupt: print(Fore.YELLOW + "\n🛑 Tool đã dừng bởi người dùng (Ctrl+C)")
    finally: print(Fore.CYAN + "Cảm ơn bạn đã sử dụng tool!")
