# pds_core.py
# 喬鈞心學 PDS - 核心運算邏輯庫 (核心邏輯 V4.5 融合版)
# 性情統計 (1-3-5-2) 與 內心數字修正 (M+O)
# 曼格拉/九能量運算引擎 (NineEnergyNumerology)

import datetime
import unicodedata

# ==========================================
# 1. 基礎數學工具
# ==========================================
def get_digit_sum(n):
    return sum(int(d) for d in str(n))

def get_single_digit(n):
    while n > 9: n = get_digit_sum(n)
    return n

def format_tradition(n):
    path = [str(n)]; curr = n
    while curr > 9: curr = get_digit_sum(curr); path.append(str(curr))
    if len(path) == 1: return path[0]
    return f"{''.join(path[:-1])}/{path[-1]}"

# ==========================================
# 2. 姓名學邏輯 (包含性情統計)
# ==========================================
def calculate_name_values(name):
    if not name: 
        return {
            "soul_str": "0", "soul_val": 0, "persona_str": "0", "persona_val": 0, 
            "destiny_str": "0", "destiny_val": 0, "temperament_string": "0-0-0-0"
        }
    
    name_clean = "".join(filter(str.isalpha, name.upper()))
    table = {
        'A':1,'J':1,'S':1,
        'B':2,'K':2,'T':2,
        'C':3,'L':3,'U':3,
        'D':4,'M':4,'V':4,
        'E':5,'N':5,'W':5,
        'F':6,'O':6,'X':6,
        'G':7,'P':7,'Y':7,
        'H':8,'Q':8,'Z':8,
        'I':9,'R':9
    }
    
    temp_counts = {"body": 0, "mental": 0, "emotional": 0, "intuitive": 0}
    vowels_set = {'A','E','I','O','U'}
    sum_soul = 0; sum_persona = 0

    for char in name_clean:
        if char in table:
            val = table[char]
            if char in vowels_set: sum_soul += val
            else: sum_persona += val
            
            # 性情分類
            if val in [4, 5]: temp_counts["body"] += 1
            elif val in [1, 8]: temp_counts["mental"] += 1
            elif val in [2, 3, 6]: temp_counts["emotional"] += 1
            elif val in [7, 9]: temp_counts["intuitive"] += 1

    sum_destiny = sum_soul + sum_persona
    temp_str = f"{temp_counts['body']}-{temp_counts['mental']}-{temp_counts['emotional']}-{temp_counts['intuitive']}"

    return {
        "soul_str": format_tradition(sum_soul),
        "soul_val": get_single_digit(sum_soul),
        "persona_str": format_tradition(sum_persona),
        "persona_val": get_single_digit(sum_persona),
        "destiny_str": format_tradition(sum_destiny),
        "destiny_val": get_single_digit(sum_destiny),
        "temperament_string": temp_str 
    }

# ==========================================
# 3. PDS 全方位三角形演算法 (M+O)
# ==========================================
def calculate_triangle_full(y, m, d):
    s_d, s_m, s_y = f"{d:02d}", f"{m:02d}", f"{y:04d}"
    A, B, C, D = int(s_d[0]), int(s_d[1]), int(s_m[0]), int(s_m[1])
    E, F, G, H = int(s_y[0]), int(s_y[1]), int(s_y[2]), int(s_y[3])

    I, J, K, L = map(get_single_digit, [A+B, C+D, E+F, G+H])
    M = get_single_digit(I+J)
    N = get_single_digit(K+L)
    O = get_single_digit(M+N)
    
    # 衛星參數 (簡略)
    present_numbers = {A,B,C,D,E,F,G,H,I,J,K,L,M,N,O}
    missing = [str(n) for n in range(1, 10) if n not in present_numbers]

    return {
        "地基": {"I": I, "J": J, "K": K, "L": L},
        "核心": {"M": M, "N": N, "O": O},
        "anchor": f"{M}{N}{O}",
        "advanced": {
            "inner": get_single_digit(M + O),
            "thinking": f"{I}{M}{O}",
            "subconscious": get_single_digit(I+L+O),
            "peak": f"{J}{I}{N}",
            "relationship": f"{K}{L}{N}",
            "missing": ",".join(missing)
        }
    }

# ==========================================
# 4. 綜合分析主介面
# ==========================================
def calculate_chart(birthdate, eng_name):
    y, m, d = birthdate.year, birthdate.month, birthdate.day
    all_sum = sum(int(c) for c in f"{y:04d}{m:02d}{d:02d}")
    
    name_data = calculate_name_values(eng_name)
    tri = calculate_triangle_full(y, m, d)
    
    lpn_single = get_single_digit(all_sum)
    current_year = datetime.date.today().year
    py_num = get_single_digit(sum(int(c) for c in str(current_year)) + m + d)
    mat_val = lpn_single + name_data['destiny_val']
    
    return {
        "age": datetime.date.today().year - y,
        "lpn": format_tradition(all_sum),
        "soul": name_data['soul_str'],
        "special": name_data['persona_str'],
        "career": name_data['destiny_str'],
        "temperament": name_data['temperament_string'], # ✅ 這裡就是 Key!
        "inner": tri['advanced']['inner'],
        "py": py_num,
        "anchor": tri['anchor'],
        "maturity": get_single_digit(mat_val),
        "restrict": tri['核心']['M'],
        "svg_params": {
            'O': tri['核心']['O'], 'M': tri['核心']['M'], 'N': tri['核心']['N'],
            'I': tri['地基']['I'], 'J': tri['地基']['J'], 'K': tri['地基']['K'], 'L': tri['地基']['L']
        }
    }

# ==========================================
# 5. 家族動力運算
# ==========================================
def calculate_family_dynamics(members_data):
    radar_counts = {i: 0 for i in range(1, 10)}
    total_weight = 0
    for member in members_data:
        p = member['params']
        radar_counts[p['O']] += 3
        for k in ['M', 'N', 'I', 'J', 'K', 'L']:
            radar_counts[p[k]] += 1
        total_weight += 9

    radar_percent = {k: round((v / total_weight) * 100, 1) for k, v in radar_counts.items()}
    reconciliation_tips = []
    scripts = {1: "「我看到你的獨立與堅持...」", 2: "「我感受到你的細膩...」", 8: "「我察覺到你的責任感...」"}

    for i, A in enumerate(members_data):
        for j, B in enumerate(members_data):
            if i == j: continue
            if A['params']['M'] == B['params']['O']:
                num = B['params']['O']
                reconciliation_tips.append({
                    "from": A['name'], "to": B['name'], "trigger_num": num,
                    "script": scripts.get(num, f"「我察覺到你的 {num} 號能量正在閃耀...」")
                })
    return {"radar_data": radar_percent, "tips": reconciliation_tips}

def calculate_family_dynamics(members):
    """
    計算家族成員之間的動力關係
    回傳格式: {'tips': [{'to': 'Name', 'script': 'Message'}]}
    """
    tips = []
    
    # 如果只有一個人
    if len(members) < 2:
        return {
            'tips': [{
                'to': members[0]['name'], 
                'script': "自己與自己的對話，是所有關係的起點。看著這個雷達圖，哪一個面向是你目前最強大的支柱？"
            }]
        }
    
    # 簡單的兩兩關係分析 (以第一個人為主詞，對其他人說話)
    main_person = members[0]
    others = members[1:]
    
    for other in others:
        mp_o = main_person['params']['O']
        op_o = other['params']['O']
        
        diff = abs(mp_o - op_o)
        msg = ""
        
        # 簡單的生剋邏輯示意 (您可以換成更複雜的邏輯)
        if mp_o == op_o:
            msg = f"你們是鏡像關係 ({mp_o}號)。你看對方不順眼的地方，通常是你自己還沒接納的部分；你欣賞對方的，也是你擁有的天賦。"
        elif (mp_o + op_o) == 10: # 例如 1+9, 2+8
            msg = f"你們是互補關係 ({mp_o} vs {op_o})。這是一場靈魂的合作，對方的強項剛好彌補你的盲點，請學會依賴對方。"
        elif diff % 3 == 0: # 3-6-9, 1-4-7
            msg = f"你們擁有相似的能量流動頻率。溝通起來應該很順暢，是能夠互相充電的好夥伴。"
        else:
            msg = f"你們來自不同的能量維度。這段關係是來擴張你的舒適圈的，試著用對方的視角看世界。"
            
        tips.append({
            'to': other['name'],
            'script': msg
        })
        
    return {'tips': tips}    

# ==========================================
# 6. 九能量系統核心運算引擎 (Nine Energy Numerology Engine)
# ==========================================
class NineEnergyNumerology:
    """
    九能量系統核心運算引擎 (Nine Energy Numerology Engine)
    包含：曼格拉/畢達哥拉斯系統 (高峰與挑戰/流年階段)
    """

    @staticmethod
    def reduce_to_single_digit(num, keep_master=False):
        """
        數字化約函式 (Theosophical Reduction)
        將數字不斷相加直到個位數 (1-9)。
        :param keep_master: 若為 True，則保留 11, 22, 33 不化約 (視需求開啟)
        """
        while num > 9:
            if keep_master and num in [11, 22, 33]:
                return num
            num = sum(int(digit) for digit in str(num))
        return num

    def calculate_diamond_chart(self, year, month, day):
        """
        計算曼格拉/畢達哥拉斯「鑽石圖」 (Pinnacles & Challenges)
        :param year: 西元出生年 (YYYY)
        :param month: 出生月 (MM)
        :param day: 出生日 (DD)
        :return: Dictionary 包含四個階段的年齡區間、高峰數、挑戰數
        """
        
        # 1. 基礎數字化約 (Base Reductions)
        m_digit = self.reduce_to_single_digit(month)
        d_digit = self.reduce_to_single_digit(day)
        y_digit = self.reduce_to_single_digit(year)
        
        # 2. 計算生命道路 (Life Path) 用於決定第一階段結束時間
        life_path = self.reduce_to_single_digit(m_digit + d_digit + y_digit)
        
        # 3. 計算時間軸 (The Timeline)
        age_end_1 = 36 - life_path
        age_end_2 = age_end_1 + 9
        age_end_3 = age_end_2 + 9
        
        # 4. 計算高峰數 (Pinnacles - 上半圓)
        pinnacle_1 = self.reduce_to_single_digit(m_digit + d_digit)
        pinnacle_2 = self.reduce_to_single_digit(d_digit + y_digit)
        pinnacle_3 = self.reduce_to_single_digit(pinnacle_1 + pinnacle_2)
        pinnacle_4 = self.reduce_to_single_digit(m_digit + y_digit)

        # 5. 計算挑戰數 (Challenges - 下半圓)
        challenge_1 = abs(m_digit - d_digit)
        challenge_2 = abs(d_digit - y_digit)
        challenge_3 = abs(challenge_1 - challenge_2)
        challenge_4 = abs(m_digit - y_digit)

        return {
            "meta": {
                "birthday": f"{year}/{month:02d}/{day:02d}",
                "life_path": life_path
            },
            "timeline": [
                {
                    "stage": "第一階段 (早年)",
                    "age_range": f"0 ~ {age_end_1} 歲",
                    "p_val": pinnacle_1,
                    "c_val": challenge_1
                },
                {
                    "stage": "第二階段 (青年/中年)",
                    "age_range": f"{age_end_1 + 1} ~ {age_end_2} 歲",
                    "p_val": pinnacle_2,
                    "c_val": challenge_2
                },
                {
                    "stage": "第三階段 (中年/壯年)",
                    "age_range": f"{age_end_2 + 1} ~ {age_end_3} 歲",
                    "p_val": pinnacle_3,
                    "c_val": challenge_3
                },
                {
                    "stage": "第四階段 (晚年)",
                    "age_range": f"{age_end_3 + 1} 歲以後",
                    "p_val": pinnacle_4,
                    "c_val": challenge_4
                }
            ]
        }