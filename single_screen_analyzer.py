import re
from urllib.parse import parse_qs, urlparse
import time
import random
import math
import os
from typing import Dict, Any, List, Tuple

# ==============================================================================
# CONFIGURATION
# ==============================================================================

LINK_FILE_NAME: str = "link_game.txt"
DEFAULT_GAME_ID: str = "PTG2008" 

# Header จำลองสำหรับวิเคราะห์ Title/Date (ไม่จำเป็นต้องแก้ไข)
MHTML_HEADER_SIMULATION: str = """
Date: Thu, 16 Oct 2025 23:42:31 +0700
Subject: =?utf-8?Q?=E0=B8=A8=E0=B8=B6=E0=B8=81=E0=B8=8A=E0=B8=B4=E0=B8=87=E0=B9=80?=
"""

# ==============================================================================
# BOT CLASS: MHTML_MINI_BOT (Core Logic)
# ==============================================================================

class MHTML_MINI_BOT:
    """จำลองฟังก์ชันเดิมพันในเกม 'ศึกชิงเจ้าไซอิ๋ว' สำหรับ 1 ลิงก์/1 เซสชัน"""

    CHIP_VALUES: List[int] = [2, 5, 10, 50, 100, 500]
    ALL_OPTIONS: List[str] = ['B (แดง)', 'T (เขียว)', 'P (ทอง)'] 
    
    def __init__(self, game_url: str, header_content: str):
        self.game_url: str = game_url
        self.content: str = header_content
        self.bet_state: Dict[str, int] = {} 
        self.total_turnover: int = 0
        self.data: Dict[str, Any] = self._analyze_metadata() 

    def _analyze_metadata(self) -> Dict[str, Any]:
        """วิเคราะห์ข้อมูลเบื้องต้นจาก URL และ Header จำลอง"""
        
        # 1. Title/Date (ใช้ค่าคงที่เพื่อความกระชับ)
        title = "ศึกชิงเจ้าไซอิ๋วสู้ไม่เคยแพ้" 
        date_match = re.search(r'Date: (.+)', self.content)
        date = date_match.group(1).strip() if date_match else "N/A"
        
        # 2. Extract Game ID
        game_id = DEFAULT_GAME_ID
        if self.game_url != "N/A":
            query_string = urlparse(self.game_url).query
            params = parse_qs(query_string)
            game_id = params.get('game', [DEFAULT_GAME_ID])[0]
        
        return {'Date': date, 'URL': self.game_url, 'ID': game_id, 'Title': title}

    def _round_to_nearest_chip(self, amount: float) -> int:
        """ปัดเศษมูลค่าที่ต้องการให้ลงตัวกับชิปที่เล็กที่สุด (2 บาท)"""
        rounded_amount = math.floor(amount / 2) * 2
        return max(0, rounded_amount)

    # --------------------------------------------------------------------------
    # #1 CUSTOM BETTING
    # --------------------------------------------------------------------------

    def func_custom_bet(self, option_keys: str, chip_value: int, click_count: str):
        """กำหนดการคลิกเหรียญและจำนวนครั้ง: B, P, หรือ B&T&P"""
        
        target_options: List[str] = []
        if option_keys == 'B': target_options = ['B (แดง)']
        elif option_keys == 'P': target_options = ['P (ทอง)']
        elif option_keys == 'B&T&P': target_options = self.ALL_OPTIONS
        else: return

        print(f"\n| #1 CUSTOM BET: {option_keys} | Chip: {chip_value} |")
        
        clicks = random.randint(1, 5) if click_count == 'random' else int(click_count)
        
        print(f"   [1.1] CHIP SELECT: {chip_value}")
        
        for option in target_options:
            placed_value = clicks * chip_value
            print(f"   [1.2] PLACING BET: คลิก {option} x {clicks} (รวม {placed_value})")
            
            self.bet_state[option] = self.bet_state.get(option, 0) + placed_value
            self.total_turnover += placed_value
            
        print(f"   [1.3] FINAL BETS: B={self.bet_state.get('B (แดง)', 0)}, P={self.bet_state.get('P (ทอง)', 0)}")


    # --------------------------------------------------------------------------
    # #2 WEIGHTED RANDOM BETTING
    # --------------------------------------------------------------------------

    def func_random_weighted_bet(self, target_turnover_hourly: int, num_spins_per_hour=100):
        """สุ่มเดิมพัน 49.9% vs 50.1% คำนวณให้ลงตัวกับชิป"""
        
        avg_bet_per_spin = target_turnover_hourly / num_spins_per_hour
        print(f"\n| #2 RANDOM BET: Target {target_turnover_hourly} B/Hr |")
        
        # 1. สุ่มยอดรวมและปัดให้ลงตัวกับชิป
        random_amount = random.uniform(avg_bet_per_spin * 0.9, avg_bet_per_spin * 1.1)
        total_bet_for_spin = self._round_to_nearest_chip(random_amount)

        if total_bet_for_spin == 0:
            print("   [WARNING] มูลค่าเดิมพันรวมเป็น 0. ข้ามรอบนี้.")
            return

        # 2. เลือกฝั่งน้ำหนักหลัก (50.1%)
        main_option: str = 'B (แดง)' if random.random() < 0.501 else 'P (ทอง)'
        side_option: str = 'P (ทอง)' if main_option == 'B (แดง)' else 'B (แดง)'
            
        # 3. แบ่งมูลค่าตามสัดส่วน (65% / 35%) และปัดเศษ
        bet_on_main: int = self._round_to_nearest_chip(total_bet_for_spin * 0.65)
        bet_on_side: int = self._round_to_nearest_chip(total_bet_for_spin - bet_on_main)
        
        actual_total_bet = bet_on_main + bet_on_side
        
        print(f"   [2.1] ACTUAL TOTAL: {actual_total_bet}")
        print(f"   [2.2] Main Bet ({main_option}, 65%): {bet_on_main}")
        print(f"   [2.3] Side Bet ({side_option}, 35%): {bet_on_side}")
        
        self.bet_state = {main_option: bet_on_main, side_option: bet_on_side}
        self.total_turnover += actual_total_bet
        
    def func_confirm_bet(self):
        """กดปุ่ม 'เดิมพันต่อ' (ยืนยัน/เริ่มเล่น)"""
        if sum(self.bet_state.values()) == 0:
             return
        print("\n   ================================================")
        print("   [ACTION] กดปุ่ม 'เดิมพันต่อ' (Confirm/Start Game)")
        print("   ================================================")
        self.bet_state = {} 
        return True

    def run_screen_session(self, target_turnover: int):
        """รันการจำลอง 1 เซสชันสำหรับ 1 ลิงก์/หน้าจอ"""
        
        print("\n-----------------------------------------------------")
        print(f"| เริ่มเซสชัน: {self.data['Title']} (ID: {self.data['ID']})")
        print(f"| URL: {self.game_url[:70]}...")
        print("-----------------------------------------------------")
        
        # --- กลยุทธ์การเดิมพันที่กำหนด ---
        
        # 1. การเดิมพันแบบ Custom (B 50 x 5)
        self.func_custom_bet(option_keys='B', chip_value=50, click_count='5')
        self.func_confirm_bet()
        
        # 2. การเดิมพันแบบ Weighted Random (อิงจากยอดเทิร์นที่กำหนด)
        self.func_random_weighted_bet(target_turnover_hourly=target_turnover)
        self.func_confirm_bet()
        
        print(f"\n[SUMMARY] เซสชันนี้ทำยอดเทิร์น: {self.total_turnover}")
        print("-----------------------------------------------------")


# ==============================================================================
# 3. RUNNER LOGIC (การจัดการหลายลิงก์)
# ==============================================================================

def load_all_links(file_name: str) -> List[str]:
    """อ่านลิงก์ทั้งหมดจากไฟล์"""
    links: List[str] = []
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url and url.startswith("http"):
                        links.append(url)
            print(f"| [INFO] พบ {len(links)} ลิงก์ใน {file_name}")
        except Exception as e:
            print(f"| [ERROR] ไม่สามารถอ่านไฟล์ {file_name}: {e}")
    else:
        print(f"| [CRITICAL] ไม่พบไฟล์ {file_name} กรุณาสร้างและใส่ลิงก์เกม")
    return links

if __name__ == "__main__":
    
    # --- การตั้งค่าที่ผู้ใช้ต้องกำหนด ---
    TARGET_TURNOVER_HOURLY: int = 10000 
    
    game_links = load_all_links(LINK_FILE_NAME)
    
    if not game_links:
        print("\n!!! การรันล้มเหลว: กรุณาตรวจสอบไฟล์ link_game.txt !!!")
    else:
        GRAND_TOTAL_TURNOVER: int = 0
        
        print("=====================================================")
        print(f"| 🤖 MINI-BOT V1.0 - MULTI-SCREEN DEMO ({len(game_links)} Sessions) |")
        print(f"| TARGET HOURLY TURNOVER: {TARGET_TURNOVER_HOURLY} B/Hr")
        print("=====================================================")
        
        for i, link in enumerate(game_links):
            print(f"\n=== SESSION {i+1}/{len(game_links)} ===")
            
            # สร้าง Bot Instance สำหรับแต่ละลิงก์
            bot = MHTML_MINI_BOT(game_url=link, header_content=MHTML_HEADER_SIMULATION)
            
            # รันการจำลองการเดิมพัน
            bot.run_screen_session(target_turnover=TARGET_TURNOVER_HOURLY)
            
            GRAND_TOTAL_TURNOVER += bot.total_turnover
            
        print("\n=====================================================")
        print(f"| ✅ ALL SESSIONS COMPLETE |")
        print(f"| GRAND TOTAL TURNOVER (DEMO): {GRAND_TOTAL_TURNOVER} |")
        print("=====================================================")
  
