import datetime
import json
import os
import warnings
import requests
import FinanceDataReader as fdr
import numpy as np
import pandas as pd
import yfinance as ticker_api

warnings.filterwarnings("ignore")

# =========================================================================
# ⚙️ [보안 안전 조치] GitHub 비밀 금고(Secrets)에서 토큰을 가져옵니다.
# =========================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ENABLE_AUTO_TELEGRAM = True          # True: 조건 만족 종목 자동 발송
FORCE_MANUAL_SEND = True             # 💡 첫 테스트를 위해 무조건 발송(True)으로 설정해 두었습니다. 
                                     # 나중에 잘 오면 False로 바꾸시면 '● 적정 가치' 기업만 알림이 갑니다.
# =========================================================================

# [고도화된 데이터 풀 구조 유지]
ai_roadmap = {
    "W1_반도체_HBM_설계_공정장비": {
        "NVDA": {"name": "엔비디아", "desc": "글로벌 독점 AI GPU 및 CUDA 생태계 선두"},
        "AMD": {"name": "AMD", "desc": "엔비디아 대항마 고성능 AI GPU 및 CPU 제조"},
        "AVGO": {"name": "브로드컴", "desc": "커스텀 AI 칩(ASIC) 및 네트워크 반도체 강자"},
        "ASML": {"name": "ASML", "desc": "초미세 공정 필수 EUV 노광장비 세계 독점 공급"},
        "TSM": {"name": "TSMC", "desc": "글로벌 1위 파운드리 및 AI 칩 위탁생산 독점"},
        "MU": {"name": "마이크론", "desc": "미국 최대 메모리 반도체 및 HBM3E 공급사"},
        "QCOM": {"name": "퀄컴", "desc": "온디바이스 AI 칩 및 모바일 AP 설계 선두"},
        "ARM": {"name": "ARM홀딩스", "desc": "저전력 반도체 설계 자산(IP) 라이선스 독점"},
        "AMAT": {"name": "어플라이드머티", "desc": "글로벌 1위 반도체 전공정 증착·이온주입 장비"},
        "KLAC": {"name": "KLA", "desc": "반도체 수율 관리를 위한 계측·검사 장비 독점"},
        "TER": {"name": "테라다인", "desc": "반도체 후공정 웨이퍼 및 패키징 테스트 장비"},
        "8035.T": {"name": "도쿄일렉트론", "desc": "일본 1위 반도체 세정 및 식각 장비 전문"},
        "000660.KS": {"name": "SK하이닉스", "desc": "글로벌 최고 수준의 HBM 메모리 시장 지배력"},
        "MRVL": {"name": "마벨 테크놀로지", "desc": "AI 고속 데이터 인프라 및 맞춤형 주문형 반도체(ASIC) 선두"},
        "005930.KS": {"name": "삼성전자", "desc": "메모리 1위 및 턴키 반도체 제조 역량 보유"},
        "042700.KQ": {"name": "한미반도체", "desc": "HBM 필수 공정 장비인 TC 본더 압도적 선두"},
        "031980.KQ": {"name": "피에스케이홀딩스", "desc": "HBM 세정 및 리플로우 후공정 기기 제조"},
        "005290.KS": {"name": "동진쎄미켐", "desc": "노광 공정 핵심 소재 포토레지스트 국산화"},
        "108320.KQ": {"name": "실리콘투", "desc": "K-뷰티 글로벌 인프라 플랫폼 및 AI 물류 최적화"},
        "110990.KQ": {"name": "디아이티", "desc": "HBM 수율 향상용 레이저 어닐링 장비 주자"},
        "039030.KQ": {"name": "이오테크닉스", "desc": "반도체 웨이퍼 다이싱용 레이저 장비 전문"},
        "240810.KQ": {"name": "원익IPS", "desc": "반도체 전공정 ALD/CVD 박막 증착 장비"},
        "ALAB": {"name": "아스트라렙스", "desc": "데이터센터 내부 고속 데이터 전송 커넥터 칩"},
        "RMBS": {"name": "램버스", "desc": "고속 메모리 인터페이스 IP 설계 및 보안"},
        "INTC": {"name": "인텔", "desc": "전통의 x86 CPU 강자 및 파운드리 재도약 도전 기업"},
        "WDC": {"name": "샌디스크", "desc": "웨스턴 디지털 산하의 글로벌 낸드 플래시 메모리 선두"},
        "IBM": {"name": "IBM", "desc": "기업용 하이브리드 클라우드, AI 플랫폼 및 양자 컴퓨터 선두"}
    },
    "W2_전력설비_변압기_광통신_원자재": {
        "VRT": {"name": "버티브", "desc": "AI 데이터센터 액체냉각 및 전력 관리 1위"},
        "GEV": {"name": "GE버노바", "desc": "초대형 가스터빈 및 송배전 그리드 인프라"},
        "CAT": {"name": "캐터필러", "desc": "데이터센터 비상 전력용 발전기 및 중장비"},
        "FCX": {"name": "프리포트맥모란", "desc": "전력망 핵심 원자재인 구리 채굴 세계 최대"},
        "ETN": {"name": "이튼", "desc": "데이터센터 전기 제어 및 고전압 배전 시스템"},
        "PWR": {"name": "콴타서비스", "desc": "북미 최대 전력망 및 신재생 인프라 시공사"},
        "HUBB": {"name": "허벨", "desc": "송전탑 자재 및 전력 배선 기기 기계 공급"},
        "GLW": {"name": "코닝", "desc": "데이터센터 초고밀도 연결용 광케이블 공급"},
        "LITE": {"name": "루멘텀", "desc": "광트랜시버용 고성능 레이저 소자 원천 기술"},
        "COHR": {"name": "코히런트", "desc": "고속 네트워킹용 800G/1.6T 광트랜시버 선두"},
        "267260.KS": {"name": "HD현대일렉트릭", "desc": "북미 공급 위주의 변압기·전력기기 최대 수혜"},
        "010120.KS": {"name": "LS일렉트릭", "desc": "국내 배전반 및 초고압 직류송전(HVDC) 선두"},
        "103590.KS": {"name": "일진전기", "desc": "초고압 변압기 및 전력 케이블 턴키 제조"},
        "006260.KS": {"name": "LS", "desc": "해저 케이블 및 구리 가공을 이끄는 인프라 지주"},
        "033100.KQ": {"name": "제룡전기", "desc": "미국 수출 중심의 중소형 배전 변압기 특화"},
        "010170.KS": {"name": "대한광통신", "desc": "광케이블 핵심 소재 광섬유 모재 자체 생산"},
        "062040.KS": {"name": "산일전기", "desc": "글로벌 빅테크 데이터센터향 특수 변압기 제조"},
        "000670.KS": {"name": "영풍정밀", "desc": "산업 인프라용 특수 펌프 및 밸브 기자재"}
    },
    "W3_데이터센터_네오클라우드_리츠_원전": {
        "EQIX": {"name": "에퀴닉스", "desc": "글로벌 최대 규모의 AI 특화 데이터센터 리츠"},
        "DLR": {"name": "디지털리얼티", "desc": "전 세계 하이퍼스케일 코로케이션 리츠 기업"},
        "AMT": {"name": "아메리칸타워", "desc": "통신탑 리츠 자산과 데이터센터 인프라 융합"},
        "AMZN": {"name": "아마존", "desc": "글로벌 1위 AWS 클라우드 및 AI 인프라 구축"},
        "SMR": {"name": "뉴스케일파워", "desc": "미국 설계인증을 획득한 소형모듈원전(SMR) 선두"},
        "CEG": {"name": "콘스텔레이션", "desc": "미국 최대 원전 공급사, 빅테크에 무탄소 전력 공급"},
        "VST": {"name": "비스트라", "desc": "원전 및 가스 발전 기반의 AI 센터 전력 도매"},
        "OKLO": {"name": "오클로", "desc": "샘 올트먼이 의장인 차세대 고속 소형 원전 개발사"},
        "IREN": {"name": "아이렌", "desc": "신재생에너지 기반 AI 클라우드 인프라 호스팅"},
        "NBIS": {"name": "네비우스", "desc": "유럽 중심 GPU 인프라 제공 네오 클라우드"},
        "CRWV": {"name": "코어위브", "desc": "엔비디아 동맹 기반의 AI 전문 클라우드 강자"},
        "APLD": {"name": "어플라이드디지털", "desc": "하이퍼스케일 AI 컴퓨팅 데이터센터 시공·디자인"},
        "034020.KS": {"name": "두산에너빌리티", "desc": "글로벌 원전 주기기 제작 및 SMR 파운드리 추진"},
        "012450.KS": {"name": "한화에어로스페이스", "desc": "우주항공 인프라 및 특수 에너지 장비 제조"},
        "272210.KS": {"name": "한화시스템", "desc": "저궤도 위성통신 인프라 및 방산 AI 소프트웨어"},
        "015760.KS": {"name": "한국전력", "desc": "국내 전력망 독점 및 해외 원전 수출 주도 공기업"}
    },
    "W4_에이전트_LLM_AI서비스_소프트웨어": {
        "MSFT": {"name": "마이크로소프트", "desc": "애저 클라우드 및 코파일럿 AI 생태계 주도"},
        "GOOGL": {"name": "구글(알파벳)", "desc": "제미나이 LLM 및 검색·안드로이드 생태계 독점"},
        "META": {"name": "메타", "desc": "오픈소스 라마(Llama) LLM 생태계 대표 주자"},
        "PLTR": {"name": "팔란티어", "desc": "정부·기업용 빅데이터 AI 분석 플랫폼 폭발 성장"},
        "CRM": {"name": "세일즈포스", "desc": "SaaS 소프트웨어 기반 자율형 AI 에이전트 도입"},
        "NOW": {"name": "서비스나우", "desc": "기업 업무 자동화 워크플로우 내 생성형 AI 탑재"},
        "SNOW": {"name": "스노우플레이크", "desc": "AI 연산용 기업 멀티 클라우드 데이터 웨어하우스"},
        "MSTR": {"name": "마이크로스트레티지", "desc": "BI 소프트웨어 기업 및 대규모 비트코인 보유"},
        "035420.KS": {"name": "NAVER", "desc": "하이퍼클로바X 중심의 토종 AI 생태계 수호"},
        "035720.KS": {"name": "카카오", "desc": "카카오톡 채널 연계 밀착형 AI 에이전트 서비스"},
        "259960.KS": {"name": "크래프톤", "desc": "게임 제작 내 딥러닝 기술 및 버추얼 프렌드 AI 개발"},
        "304100.KQ": {"name": "솔트룩스", "desc": "국내 공공·기업 맞춤형 온프레미스 LLM 구축"}
    },
    "W5_응용_수익화_끝단_애플리케이션": {
        "TTD": {"name": "더트레이드데스크", "desc": "AI 기반 디지털 광고 구매 자동화 플랫폼"},
        "SHOP": {"name": "쇼피파이", "desc": "이커머스 인프라 내 셀러용 AI 코파일럿 제공"},
        "CRWD": {"name": "크라우드스트라이크", "desc": "클라우드 기반 AI 엔드포인트 사이버 보안 선두"},
        "SIEGY": {"name": "지멘스", "desc": "독일 대표 스마트 팩토리 공정 자동화 솔루션"},
        "DASTY": {"name": "다쏘시스템", "desc": "디지털 트윈 구현을 위한 3D 설계·시뮬레이션"},
        "CGNX": {"name": "코그넥스", "desc": "공장 라인 불량 검사용 AI 머신비전 시스템"},
        "454910.KS": {"name": "두산로보틱스", "desc": "국내 1위 협동로봇 제조 및 AI 인지 제어 국산화"},
        "098460.KQ": {"name": "고영", "desc": "반도체 SMT 공정용 3차원 AI 검사장비 세계 선두"},
        "348340.KQ": {"name": "뉴로메카", "desc": "중소 제조업용 협동로봇 및 제어 알고리즘 개발"},
        "267250.KS": {"name": "HD현대", "desc": "선박 자율운항 및 스마트 십야드 AI 전환 주도"}
    },
    "W6_피지컬AI_로봇_우주항공_자율주행": {
        "TSLA": {"name": "테슬라", "desc": "FSD 자율주행 기술 및 옵티머스 휴머노이드 개발"},
        "AAPL": {"name": "애플", "desc": "아이폰 기반 온디바이스 애플 인텔리전스 생태계"},
        "UBER": {"name": "우버", "desc": "모빌리티 매칭 최적화 및 자율주행 로보택시 제휴"},
        "PANW": {"name": "팔로알토네트웍스", "desc": "차세대 클라우드 보안 및 AI 기반 플랫폼 통합"},
        "277810.KS": {"name": "레인보우로보틱스", "desc": "이족보행 기술력 바탕 삼성 로봇 밸류체인 진입"},
        "005380.KS": {"name": "현대차", "desc": "SDV 전환 및 보스턴 다이내믹스 로봇 융합 추진"},
        "000270.KS": {"name": "기아", "desc": "목적 기반 모빌리티(PBV) 인프라 전문 메이커"},
        "086280.KS": {"name": "현대글로비스", "desc": "스마트 물류 자동화 및 AI 배차 경로 최적화"},
        "012330.KS": {"name": "현대모비스", "desc": "자율주행 섀시 부품 및 차량용 소프트웨어 공급"},
        "204320.KS": {"name": "HL만도", "desc": "전자제어 조향·제동 스마트 아키철처 인프라"},
        "058610.KS": {"name": "에스피지", "desc": "로봇 관절용 정밀 감속기(SR) 국산화 선두 주자"},
        "389500.KS": {"name": "에스비비테크", "desc": "하모닉 감속기 치형 설계 및 초정밀 가공 특화"},
        "092200.KS": {"name": "디아이씨", "desc": "차량 구동계 기어 및 로봇 감속기 양산 인프라"},
        "6324.T": {"name": "하모닉 드라이브", "desc": "로봇 관절 필수 파동 감속기 세계 1위 점유율"},
        "6268.T": {"name": "나브테스코", "desc": "중대형 산업 로봇 관절용 정밀 RV 감속기 제조"},
        "108490.KQ": {"name": "로보티즈", "desc": "자율주행, 서비스로봇 솔루션 제공"}
    }
}

# 기술적 퀀트 지표: RSI 계산 함수
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def analyze_stock_metrics(ticker_symbol, company_info):
    try:
        company_name = company_info["name"]
        
        is_korean = ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ")
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=120)

        # 1. 주가 데이터 가져오기
        if is_korean:
            pure_code = ticker_symbol.split(".")[0]
            df_60 = fdr.DataReader(pure_code, start=start_date, end=end_date)
        else:
            stock = ticker_api.Ticker(ticker_symbol)
            df_60 = stock.history(start=start_date, end=end_date)

        if df_60.empty or len(df_60) < 20:
            return None

        df = df_60.tail(5)
        current_price = df["Close"].iloc[-1]
        prev_price = df["Close"].iloc[-2]
        price_change_pct = ((current_price - prev_price) / prev_price) * 100

        # 퀀트 계산 A: 실시간 RSI 모멘텀 계산
        rsi_val = calculate_rsi(df_60["Close"], 14)
        rsi_val = round(rsi_val, 1) if not np.isnan(rsi_val) else 50.0

        # 2. 기업 재무 지표 가져오기
        yf_stock = ticker_api.Ticker(ticker_symbol)
        info = yf_stock.info

        per = info.get("forwardPE") or info.get("trailingPE")
        pbr = info.get("priceToBook")
        roe = info.get("returnOnEquity")
        if roe is not None:
            roe = roe * 100
            
        # 퀀트 계산 B: 부채 비율
        debt_to_equity = info.get("debtToEquity")
        debt_str = f"{round(debt_to_equity, 1)}%" if debt_to_equity is not None else "N/A"

        # 퀀트 계산 C: 밸류에이션 종합 스코어
        if per is not None and pbr is not None and per > 0 and pbr > 0:
            graham_mult = per * pbr
            if graham_mult <= 22.5: score = "★ 저평가 우량"
            elif graham_mult <= 50.0: score = "● 적정 가치"
            else: score = "▲ 성장 프리미엄"
        else:
            score = "중립"

        # 3. 이동평균선 기반 지표 계산
        vol_5ma = df_60["Volume"].tail(5).mean()
        vol_20ma = df_60["Volume"].tail(20).mean()
        volume_surge = vol_5ma / vol_20ma if vol_20ma > 0 else 1

        price_20ma = df_60["Close"].tail(20).mean()
        disparity = current_price / price_20ma if price_20ma > 0 else 1

        # 4. 과열 지표 로직
        if (disparity > 1.15 and volume_surge > 1.3) or rsi_val >= 75:
            status = "과열🔥"
        elif (disparity > 1.03 and volume_surge > 1.0) or (55 <= rsi_val < 75):
            status = "진행🟢"
        elif (disparity >= 0.95 and volume_surge > 0.7) or (40 <= rsi_val < 55):
            status = "임박🟡"
        else:
            status = "잠복💤"

        # 5. 국가별 통화 포맷팅
        if is_korean:
            price_str = f"{int(current_price):,}원"
        elif ticker_symbol.endswith(".T"):
            price_str = f"¥{int(current_price):,}"
        else:
            price_str = f"${current_price:.2f}"

        return {
            "company": company_name,
            "ticker": ticker_symbol,
            "price": price_str,
            "change": round(price_change_pct, 2),
            "per": round(per, 1) if per is not None else "N/A",
            "pbr": round(pbr, 1) if pbr is not None else "N/A",
            "roe": round(roe, 1) if roe is not None else "N/A",
            "rsi": rsi_val,
            "debt": debt_str,
            "qscore": score,
            "status": status,
        }
    except Exception as e:
        return None

def send_telegram_alert(stage_dict, force_manual=False):
    """텔레그램 메시지 생성 및 발송 모듈"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if force_manual:
        title = f"📢 [수동 전송] AI 밸류체인 전체 퀀트 현황 ({now_str})\n"
    else:
        title = f"🎯 [퀀트 알림] '● 적정 가치' 구간 진입 기업 포착 ({now_str})\n"
        
    message_body = ""
    total_count = 0
    
    for stage, items in stage_dict.items():
        stage_content = ""
        for item in items:
            # 자동 모드일 때는 '적정 가치' 상태만 필터링, 수동 강제 발송 모드일 때는 전부 포함
            if force_manual or "적정 가치" in item["qscore"]:
                total_count += 1
                stage_content += f" ▪️ *{item['company']}* ({item['ticker']}) - `{item['status']}`\n"
                stage_content += f"   - 퀀트 스코어: {item['qscore']}\n"
                stage_content += f"   - 현재 주가: {item['price']} ({item['change']}%)\n"
                stage_content += f"   - PER / PBR / ROE: {item['per']}배 / {item['pbr']}배 / {item['roe']}%\n"
                stage_content += f"   - RSI(14) / 부채비율: {item['rsi']} / {item['debt']}\n\n"
        
        if stage_content:
            message_body += f"\n📌 *{stage}*\n" + stage_content

    if total_count == 0:
        print("ℹ️ 텔레그램 발송 조건('적정 가치')을 만족하는 기업이 없어서 알림을 보내지 않았습니다.")
        return

    full_message = title + message_body
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    try:
        # 메시지가 텔레그램 글자 수 제한(4000자)을 넘을 수 있으므로 안전 분할 절차 실행
        if len(full_message) > 4000:
            chunks = [full_message[i:i+3500] for i in range(0, len(full_message), 3500)]
            for chunk in chunks:
                requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"})
        else:
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": full_message, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
            
        print(f"🚀 텔레그램 알림 발송 완료! (총 {total_count}개 종목 전송됨)")
    except Exception as e:
        print(f"❌ 텔레그램 통신 오류 발생: {e}")

# =========================================================================
# 메인 실행부
# =========================================================================
if __name__ == "__main__":
    print("🔄 전종목 데이터 수집 및 퀀트 스크리닝 시작...")
    all_data_json = {}
    
    for stage, ticker_dict in ai_roadmap.items():
        stage_data = []
        for ticker, info_dict in ticker_dict.items():
            res = analyze_stock_metrics(ticker, info_dict) 
            if res:
                stage_data.append(res)
        all_data_json[stage] = stage_data

    # 텔레그램 발송 로직 처리
    if FORCE_MANUAL_SEND:
        print("🔄 [수동 강제 발송 모드 작동] 조건에 상관없이 데이터를 텔레그램으로 즉시 전송합니다...")
        send_telegram_alert(all_data_json, force_manual=True)
    elif ENABLE_AUTO_TELEGRAM:
        print("🔄 [자동 알림 모드 작동] '● 적정 가치' 스코어를 획득한 기업을 검사 중...")
        send_telegram_alert(all_data_json, force_manual=False)
