# pds_core.py
# 喬鈞心學 PDS - 核心運算邏輯庫 (純淨運算版 V4.4)
# 專注於數學邏輯，不包含解釋文字，將詮釋權回歸使用者與教材。

import datetime

# ==========================================
# 1. 基礎數學工具
# ==========================================
def get_digit_sum(n):
    return sum(int(d) for d in str(n))

def get_single_digit(n):
    while n > 9: n = get_digit_sum(n)
    return n

def format_tradition(n):
    """保留多層次傳承格式 (如 3811/2)"""
    path = [str(n)]; curr = n
    while curr > 9: curr = get_digit_sum(curr); path.append(str(curr))
    if len(path) == 1: return path[0]
    return f"{''.join(path[:-1])}/{path[-1]}"

# ==========================================
# 2. 姓名學邏輯 (Pythagorean)
# ==========================================
def calculate_name_values(name):
    if not name: return {"soul_str": "0", "soul_val": 0, "persona_str": "0", "persona_val": 0, "destiny_str": "0", "destiny_val": 0}
    name = name.upper().replace(" ", "")
    
    # 數值表 (補全 I, R = 9)
    table = {
        'A':1,'J':1,'S':1,'B':2,'K':2,'T':2,'C':3,'L':3,'U':3,'D':4,'M':4,'V':4,
        'E':5,'N':5,'W':5,'F':6,'O':6,'X':6,'G':7,'P':7,'Y':7,'H':8,'Q':8,'Z':8,
        'I':9,'R':9 
    }
    vowels_set = {'A','E','I','O','U'} # Y為子音
    
    sum_soul = 0; sum_persona = 0
    for char in name:
        if char in table:
            val = table[char]
            if char in vowels_set: sum_soul += val
            else: sum_persona += val
            
    sum_destiny = sum_soul + sum_persona
    return {
        "soul_str": format_tradition(sum_soul), 
        "soul_val": get_single_digit(sum_soul),
        "persona_str": format_tradition(sum_persona), 
        "persona_val": get_single_digit(sum_persona),
        "destiny_str": format_tradition(sum_destiny), 
        "destiny_val": get_single_digit(sum_destiny)
    }

# ==========================================
# 3. PDS 全方位三角形演算法 (A-X 完整路徑)
# ==========================================
def calculate_triangle_full(y, m, d):
    # 1. 拆解 A-H
    s_d, s_m, s_y = f"{d:02d}", f"{m:02d}", f"{y:04d}"
    A, B, C, D = int(s_d[0]), int(s_d[1]), int(s_m[0]), int(s_m[1])
    E, F, G, H = int(s_y[0]), int(s_y[1]), int(s_y[2]), int(s_y[3])

    # 2. 底層 I-L
    I, J, K, L = map(get_single_digit, [A+B, C+D, E+F, G+H])

    # 3. 核心 M-O
    M = get_single_digit(I+J)
    N = get_single_digit(K+L)
    O = get_single_digit(M+N)

    # 4. 衛星 P-X
    P, Q = get_single_digit(I+M), get_single_digit(J+M)
    R = get_single_digit(P+Q) # 青年

    S, T = get_single_digit(N+O), get_single_digit(M+O)
    U = get_single_digit(S+T) # 中年

    V, W = get_single_digit(K+N), get_single_digit(L+N)
    X = get_single_digit(V+W) # 晚年

    # 5. 進階參數
    present_numbers = {A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X}
    missing = [str(n) for n in range(1, 10) if n not in present_numbers]

    return {
        "地基": {"I": I, "J": J, "K": K, "L": L},
        "核心": {"M": M, "N": N, "O": O},
        "anchor": f"{M}{N}{O}",
        "階段": {
            "youth": f"{P}{Q}{R}", 
            "middle": f"{S}{T}{U}", 
            "late": f"{V}{W}{X}"
        },
        "advanced": {
            "inner": get_single_digit(O * 2),
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
    
    # A. 生命道路
    all_sum = sum(int(c) for c in f"{y:04d}{m:02d}{d:02d}")
    lpn_str = format_tradition(all_sum)
    lpn_single = get_single_digit(all_sum)
    
    # B. 姓名數據
    name_data = calculate_name_values(eng_name)
    
    # C. 流年
    current_year = datetime.date.today().year
    py_raw = sum(int(c) for c in str(current_year)) + m + d
    py_num = get_single_digit(py_raw)
    
    # D. 三角形完整運算
    tri = calculate_triangle_full(y, m, d)
    
    # E. 成熟與制約
    mat_val = lpn_single + name_data['destiny_val']
    maturity_str = get_single_digit(mat_val)
    restrict_val = tri['核心']['M'] 
    
    return {
        "age": datetime.date.today().year - y,
        "lpn": lpn_str,
        "soul": name_data['soul_str'],        
        "special": name_data['persona_str'],  
        "career": name_data['destiny_str'],   
        "py": py_num,
        "anchor": tri['anchor'],
        "maturity": maturity_str,
        "restrict": restrict_val,
        "svg_params": {
            'O': tri['核心']['O'], 'M': tri['核心']['M'], 'N': tri['核心']['N'], 
            'I': tri['地基']['I'], 'J': tri['地基']['J'], 'K': tri['地基']['K'], 'L': tri['地基']['L']
        }
    }

# ==========================================
# 5. 家族動力運算
# ==========================================
def calculate_family_dynamics(members_data):
    """
    計算家族集體能量與和解建議
    members_data: List of dicts [{"name": str, "params": dict}, ...]
    """
    # 1. 統計 1-9 能量雷達分佈
    radar_counts = {i: 0 for i in range(1, 10)}
    total_weight = 0
    
    for member in members_data:
        p = member['params']
        # 主命數 (O) 權重設為 3
        radar_counts[p['O']] += 3
        # 其他位置 (M, N, I, J, K, L) 權重為 1
        for k in ['M', 'N', 'I', 'J', 'K', 'L']:
            radar_counts[p[k]] += 1
        total_weight += 9 # 3 + 6個位置

    radar_percent = {k: round((v / total_weight) * 100, 1) for k, v in radar_counts.items()}

    # 2. 生成和解對話模版 (利他語法)
    reconciliation_tips = []
    scripts = {
        1: "「我看到你的獨立與堅持，這份力量撐起了家，謝謝你的承擔。」",
        2: "「我感受到你的細膩與體貼，謝謝你溫柔地接住大家的感受。」",
        8: "「我察覺到你的責任感讓你壓力很大，沒關係，這份擔子我們可以一起扛。」"
    }

    # 關係衝突掃描 (以 A 的制約對應 B 的主命)
    for i, A in enumerate(members_data):
        for j, B in enumerate(members_data):
            if i == j: continue
            
            # 當 A 的壓力點(制約M) 遇到 B 的核心行為(主命O)
            if A['params']['M'] == B['params']['O']:
                num = B['params']['O']
                reconciliation_tips.append({
                    "from": A['name'],
                    "to": B['name'],
                    "trigger_num": num,
                    "script": scripts.get(num, f"「我察覺到你的 {num} 號能量正在閃耀，我也在學習如何與這份力量和諧共處。」")
                })

    return {
        "radar_data": radar_percent,
        "tips": reconciliation_tips
    }
    