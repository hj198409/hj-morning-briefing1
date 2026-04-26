# ================================
# 📊 유진투자증권 나효정 대리 모닝브리핑
# Selenium 없는 모바일 최적화 버전
# ================================
import warnings
import requests
import math
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(page_title="모닝브리핑", layout="wide")

# =========================
# 스타일
# =========================
st.markdown("""
<style>

/* 전체 배경 */
body {
    background-color: #0b1220;
}

/* 제목 */
.main-title {
    font-size: 34px;
    font-weight: 900;
    text-align: center;
    color: #ffffff;
    margin-top: 10px;
}

/* 서브 제목 */
.sub-title {
    text-align: center;
    font-size: 18px;
    color: #9ca3af;
    margin-bottom: 20px;
}

/* 카드 */
.card {
    background: #ffffff;
    border-radius: 20px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* 카드 타이틀 */
.card-title {
    font-size: 15px;
    color: #6b7280;
    font-weight: 700;
}

/* 값 */
.card-value {
    font-size: 28px;
    font-weight: 900;
    margin-top: 6px;
}

/* 상승 */
.up {
    color: #e11d48;
}

/* 하락 */
.down {
    color: #2563eb;
}

/* 모바일 대응 */
@media (max-width: 768px) {
    .main-title {
        font-size: 26px;
    }
    .card-value {
        font-size: 24px;
    }
}

</style>
""", unsafe_allow_html=True)

# =========================
# 제목
# =========================
st.markdown("""
<div class="main-title">
📊 유진투자증권 나효정 대리
</div>
<div class="sub-title">
모닝 브리핑
</div>
""", unsafe_allow_html=True)

# =========================
# 티커
# =========================
tickers = {
    "S&P500": ["^GSPC", "SPY", "^SPX"],  # 🔥 핵심
    "나스닥": "^IXIC",
    "다우": "^DJI",
    "필라델피아 반도체": "^SOX",
    "미국 10년": "^TNX",
    "미국 2년": "^IRX",
    "달러/원": "KRW=X",
    "달러/엔": "JPY=X",
    "금": "GC=F",
    "은": "SI=F",
    "구리": "HG=F",
    "WTI유가": "CL=F",
    "비트코인": "BTC-USD",
    "코스피": "^KS11",
    "코스닥": "^KQ11",
    "EWY": "EWY",
}

# =========================
# 주요 지표 데이터
# =========================
@st.cache_data(ttl=600)
def get_data(ticker):
    try:
        # 티커를 리스트로 변환 (단일 / 복수 대응)
        ticker_list = ticker if isinstance(ticker, list) else [ticker]

        for t in ticker_list:
            try:
                df = yf.download(
                    t,
                    period="1mo",
                    progress=False,
                    auto_adjust=False,
                    threads=False
                )

                if df is None or df.empty:
                    continue

                close = df["Close"]

                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]

                close = close.dropna()

                if len(close) < 2:
                    continue

                last = float(close.iloc[-1])
                prev = float(close.iloc[-2])
                pct = (last - prev) / prev * 100 if prev != 0 else 0

                return round(last, 2), round(pct, 2)

            except Exception:
                continue

        return None, None

    except Exception:
        return None, None

def draw_card(name):
    val, pct = get_data(tickers[name])

    if val is None:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">{name}</div>
            <div class="card-value flat">데이터 없음</div>
        </div>
        """, unsafe_allow_html=True)
        return

    color = "up" if pct > 0 else "down" if pct < 0 else "flat"

    st.markdown(f"""
    <div class="card">
        <div class="card-title">{name}</div>
        <div class="card-value {color}">{val:,.2f}</div>
        <div class="{color}">{pct:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)


def section(title, items):
    st.markdown(f"### {title}")
    cols = st.columns(2)

    for i, item in enumerate(items):
        with cols[i % 2]:
            draw_card(item)


# =========================
# 글로벌 공포탐욕지수 최종 안정형
# 자동연동 + 캐시 + 수동값 fallback
# =========================
import os
import json
import re
import math
import matplotlib.pyplot as plt

# 사이트 자동조회 실패 시 사용할 기본값
MANUAL_US_FEAR_GREED = 66
MANUAL_KOSPI_FEAR_GREED = 79.9

CACHE_FILE = "fear_greed_cache.json"


def set_korean_font():
    import os
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",   # Streamlit Cloud
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "C:/Windows/Fonts/malgun.ttf",                       # 내 PC
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            font_name = fm.FontProperties(fname=font_path).get_name()
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return

    # fallback
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False


def fear_greed_label(score):
    if score < 25:
        return "극도의 공포"
    elif score < 45:
        return "공포"
    elif score < 55:
        return "중립"
    elif score < 75:
        return "탐욕"
    else:
        return "극도의 탐욕"


def save_cache(us=None, kr=None):
    old = load_cache() or {}

    data = {
        "us": us if us is not None else old.get("us"),
        "kr": kr if kr is not None else old.get("kr"),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


@st.cache_data(ttl=1800)
def load_us_fear_greed():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://edition.cnn.com/markets/fear-and-greed"
        }

        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        score = data.get("fear_and_greed", {}).get("score")

        if score is not None:
            score = round(float(score), 1)
            save_cache(us=score)
            return score, fear_greed_label(score), "CNN 자동"

    except Exception:
        pass

    cache = load_cache()
    if cache and cache.get("us") is not None:
        score = float(cache["us"])
        return score, fear_greed_label(score), "캐시값"

    score = MANUAL_US_FEAR_GREED
    return score, fear_greed_label(score), "수동값"


@st.cache_data(ttl=1800)
def load_kospi_fear_greed():
    try:
        url = "https://kospi-fear-greed-index.co.kr/"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=10)
        html = res.text

        # 79.9 같은 소수점 지수값 우선 추출
        nums = re.findall(r"\b\d{2}\.\d\b", html)

        candidates = []
        for n in nums:
            v = float(n)
            if 20 <= v <= 99.9:
                candidates.append(v)

        if candidates:
            score = candidates[0]
            save_cache(kr=score)
            return score, fear_greed_label(score), "사이트 자동"

    except Exception:
        pass

    cache = load_cache()
    if cache and cache.get("kr") is not None:
        score = float(cache["kr"])
        return score, fear_greed_label(score), "캐시값"

    score = MANUAL_KOSPI_FEAR_GREED
    return score, fear_greed_label(score), "수동값"


def draw_cnn_style_gauge(title, score, label, source_text=""):
    set_korean_font()

    if score is None:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">{title}</div>
            <div class="card-value flat">데이터 없음</div>
        </div>
        """, unsafe_allow_html=True)
        return

    score = max(0, min(100, float(score)))
    angle = 180 - (score / 100 * 180)
    needle_angle = math.radians(angle)

    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    segments = [
        (0, 25, "#f3f3f3", "EXTREME\nFEAR"),
        (25, 45, "#f5f5f5", "FEAR"),
        (45, 55, "#f7f7f7", "NEUTRAL"),
        (55, 75, "#b9eee6", "GREED"),
        (75, 100, "#f3f3f3", "EXTREME\nGREED"),
    ]

    for start, end, color, _ in segments:
        theta1 = 180 - start / 100 * 180
        theta2 = 180 - end / 100 * 180

        ax.add_patch(plt.matplotlib.patches.Wedge(
            (0, 0),
            1.0,
            theta2,
            theta1,
            width=0.36,
            facecolor=color,
            edgecolor="#ffffff",
            linewidth=2
        ))

    for start, end, color, _ in segments:
        if start <= score <= end:
            theta1 = 180 - start / 100 * 180
            theta2 = 180 - end / 100 * 180

            ax.add_patch(plt.matplotlib.patches.Wedge(
                (0, 0),
                1.0,
                theta2,
                theta1,
                width=0.36,
                facecolor="#b9eee6" if score >= 55 else "#eeeeee",
                edgecolor="#39a77a",
                linewidth=1.8
            ))
            break

    for tick in [0, 25, 50, 75, 100]:
        tick_angle = math.radians(180 - tick / 100 * 180)
        ax.text(
            0.53 * math.cos(tick_angle),
            0.53 * math.sin(tick_angle),
            str(tick),
            ha="center",
            va="center",
            fontsize=12,
            color="#888888"
        )

    for tick in range(5, 100, 5):
        tick_angle = math.radians(180 - tick / 100 * 180)
        ax.scatter(
            0.58 * math.cos(tick_angle),
            0.58 * math.sin(tick_angle),
            s=4,
            color="#999999"
        )

    ax.text(-0.78, 0.45, "EXTREME\nFEAR", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#777777", rotation=70)
    ax.text(-0.45, 0.85, "FEAR", ha="center", va="center",
            fontsize=12, fontweight="bold", color="#777777", rotation=25)
    ax.text(0, 0.94, "NEUTRAL", ha="center", va="center",
            fontsize=12, fontweight="bold", color="#777777")
    ax.text(0.45, 0.85, "GREED", ha="center", va="center",
            fontsize=12, fontweight="bold", color="#222222", rotation=-25)
    ax.text(0.78, 0.45, "EXTREME\nGREED", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#777777", rotation=-70)

    nx = 0.76 * math.cos(needle_angle)
    ny = 0.76 * math.sin(needle_angle)

    ax.plot([0, nx], [0, ny], color="#222222", linewidth=5, solid_capstyle="round")
    # 중심 흰 원
    ax.scatter([0], [0], s=900, color="#ffffff", zorder=5)
    # 바늘 중심점
    ax.scatter([0], [0], s=45, color="#222222", zorder=6)

    value_text = f"{score:.0f}" if score == int(score) else f"{score:.1f}"

# 숫자를 중심점보다 아래에 배치해서 바늘과 겹치지 않게 처리
    ax.text(
    0,
    -0.11,
    value_text,
    ha="center",
    va="center",
    fontsize=28,
    fontweight="bold",
    color="#111827",
    zorder=7
    )

    ax.set_title(title, fontsize=24, fontweight="bold", loc="left", pad=10, color="#000000")
    ax.text(-1.0, -0.12, source_text, ha="left", va="center", fontsize=9, color="#6b7280")

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-0.24, 1.12)
    ax.axis("off")

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def draw_fear_greed_section():
    st.markdown("### 🌎 글로벌 공포탐욕지수")

    col1, col2 = st.columns(2)

    with col1:
        us_score, us_label, us_src = load_us_fear_greed()
        draw_cnn_style_gauge(
            "미국 공포탐욕지수",
            us_score,
            us_label,
            f"Source: {us_src}"
        )

    with col2:
        kr_score, kr_label, kr_src = load_kospi_fear_greed()
        draw_cnn_style_gauge(
            "코스피 공포탐욕지수",
            kr_score,
            kr_label,
            f"Source: {kr_src}"
        )
        
# =========================
# 시장맵 iframe - 최종 완성형
# =========================
def market_iframe(url, height=650, top_crop=340, bottom_crop=250):
    components.html(
        f"""
        <div style="
            width:100%;
            height:{height}px;
            overflow:auto;
            border-radius:14px;
            border:1px solid #d9e6f2;
            background:#20242c;
        ">
            <iframe
                src="{url}"
                style="
                    width:100%;
                    height:2000px;
                    border:0;
                    margin-top:-{top_crop}px;
                    margin-bottom:-{bottom_crop}px;
                ">
            </iframe>
        </div>
        """,
        height=height + 10,
    )


# =========================
# 글로벌 시장맵
# =========================
def draw_market_maps():
    st.markdown("### 🌎 글로벌 시장맵")

    # =========================
    # 🇺🇸 미국증시
    # =========================
    st.markdown("""
    <div class="card">
        <div class="card-title">🇺🇸 미국증시 시장맵</div>
    </div>
    """, unsafe_allow_html=True)

    market_iframe(
        "https://www.hankyung.com/globalmarket/usa-marketmap",
        height=650,
        top_crop=360   # 🔥 상단 배너 제거
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # 🇰🇷 코스피
    # =========================
    st.markdown("""
    <div class="card">
        <div class="card-title">🇰🇷 한국증시(코스피) 시장맵</div>
    </div>
    """, unsafe_allow_html=True)

    market_iframe(
        "https://markets.hankyung.com/marketmap/kospi",
        height=650,
        top_crop=335   # 🔥 한경 코리아마켓 제거
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # 🇰🇷 코스닥
    # =========================
    st.markdown("""
    <div class="card">
        <div class="card-title">🇰🇷 한국증시(코스닥) 시장맵</div>
    </div>
    """, unsafe_allow_html=True)

    market_iframe(
        "https://markets.hankyung.com/marketmap/kosdaq",
        height=650,
        top_crop=335
    )
    
# =========================
# ETF 데이터
# =========================
@st.cache_data(ttl=600)
def load_etf():
    try:
        url = "https://finance.naver.com/api/sise/etfItemList.nhn"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.naver.com/sise/etf.naver"
        }

        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        items = data.get("result", {}).get("etfItemList", [])

        if not items:
            return pd.DataFrame(), pd.DataFrame()

        df = pd.DataFrame(items)
        df = df[["itemname", "changeRate"]].copy()
        df.columns = ["종목명", "등락률"]

        df["등락률"] = pd.to_numeric(df["등락률"], errors="coerce")
        df = df.dropna(subset=["종목명", "등락률"])
        df = df.drop_duplicates(subset=["종목명"])

        up = df.sort_values("등락률", ascending=False).head(5).copy()
        down = df.sort_values("등락률", ascending=True).head(5).copy()

        up["등락률"] = up["등락률"].apply(lambda x: f"{x:+.2f}%")
        down["등락률"] = down["등락률"].apply(lambda x: f"{x:+.2f}%")

        up.index = range(1, len(up) + 1)
        down.index = range(1, len(down) + 1)

        return up, down

    except Exception:
        return pd.DataFrame(), pd.DataFrame()


def draw_etf_cards(title, df, mode="up"):
    icon = "📈" if mode == "up" else "📉"
    color_class = "up" if mode == "up" else "down"

    st.markdown(f"### {icon} {title}")

    if df.empty:
        st.info(f"{title} 데이터를 불러오지 못했습니다.")
        return

    for idx, row in df.iterrows():
        st.markdown(f"""
        <div class="etf-card">
            <div class="etf-row">
                <div>
                    <div class="etf-rank">#{idx}</div>
                    <div class="etf-name">{row["종목명"]}</div>
                </div>
                <div class="etf-rate {color_class}">
                    {row["등락률"]}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================
# 자동연동 + 백업 매크로 캘린더
# =========================
@st.cache_data(ttl=3600)
def load_macro_calendar():
    try:
        start = datetime.today().strftime("%Y-%m-%d")
        end = (datetime.today() + timedelta(days=45)).strftime("%Y-%m-%d")

        url = (
            "https://api.tradingeconomics.com/calendar/country/"
            "united%20states,south%20korea"
            f"?d1={start}&d2={end}&c=guest:guest"
        )

        res = requests.get(url, timeout=10)
        data = res.json()

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            if "Date" in df.columns and "Country" in df.columns and "Event" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                df = df.dropna(subset=["Date"])

                df["날짜"] = df["Date"].dt.strftime("%m/%d")
                df["국가"] = df["Country"].replace({
                    "United States": "미국",
                    "South Korea": "한국"
                })
                df["일정"] = df["Event"].astype(str)

                keywords = [
                    "Interest Rate", "FOMC", "CPI", "PPI",
                    "Inflation", "Unemployment", "Non Farm",
                    "Payrolls", "Retail Sales", "GDP",
                    "Consumer Confidence", "ISM"
                ]

                pattern = "|".join(keywords)
                df = df[df["일정"].str.contains(pattern, case=False, na=False)]

                if not df.empty:
                    return df[["날짜", "국가", "일정"]].sort_values("날짜")

    except Exception:
        pass

    fallback = pd.DataFrame([
        ["04/28", "미국", "FOMC 기준금리"],
        ["04/29", "미국", "FOMC 기준금리"],
        ["05/08", "미국", "실업률"],
        ["05/12", "미국", "CPI"],
        ["05/13", "한국", "실업률"],
        ["05/13", "미국", "PPI"],
        ["05/14", "한국", "옵션만기일"],
        ["05/15", "미국", "옵션만기일"],
        ["05/28", "한국", "기준금리"],
    ], columns=["날짜", "국가", "일정"])

    return fallback


def draw_macro_schedule():
    st.markdown("### 🗓️ 매크로 일정 캘린더")

    df = load_macro_calendar()

    st.markdown("""
    <style>
    .calendar-box {
        background:#ffffff;
        border-radius:16px;
        padding:14px;
        border:1px solid #d9e6f2;
        box-shadow:0 2px 6px rgba(0,0,0,0.05);
    }
    .calendar-grid {
        display:grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap:10px;
    }
    .day-card {
        background:#f8fbff;
        border-radius:12px;
        padding:10px;
        min-height:90px;
        border:1px solid #e3edf7;
    }
    .date {
        font-weight:900;
        font-size:14px;
        margin-bottom:6px;
        color:#1f2c3b;
    }
    .event-us {
        background:#eef4ff;
        color:#2457c5;
        padding:4px 6px;
        border-radius:8px;
        font-size:12px;
        margin-top:4px;
        font-weight:700;
    }
    .event-kr {
        background:#fff1f1;
        color:#d9463b;
        padding:4px 6px;
        border-radius:8px;
        font-size:12px;
        margin-top:4px;
        font-weight:700;
    }
    </style>
    """, unsafe_allow_html=True)

    dates = sorted(df["날짜"].unique().tolist())

    html = '<div class="calendar-box"><div class="calendar-grid">'

    for d in dates:
        events = df[df["날짜"] == d]

        html += f'<div class="day-card"><div class="date">{d}</div>'

        for _, row in events.iterrows():
            cls = "event-kr" if row["국가"] == "한국" else "event-us"
            html += f'<div class="{cls}">{row["국가"]} · {row["일정"]}</div>'

        html += "</div>"

    html += "</div></div>"

    st.markdown(html, unsafe_allow_html=True)

# =========================
# 출력
# =========================
section("📈 미국증시", ["S&P500", "다우", "나스닥", "필라델피아 반도체"])
section("💱 금리 / 환율", ["미국 10년", "미국 2년", "달러/원", "달러/엔"])
section("🛢️ 원자재 / 비트코인", ["금", "은", "구리", "WTI유가", "비트코인"])
section("🇰🇷 국내증시 및 ETF", ["코스피", "코스닥", "EWY"])

draw_fear_greed_section()
draw_market_maps()

etf_up, etf_down = load_etf()

st.markdown("### 📊 ETF 흐름")
draw_etf_cards("ETF 상승률 TOP 5", etf_up, mode="up")
st.markdown("<br>", unsafe_allow_html=True)
draw_etf_cards("ETF 하락률 TOP 5", etf_down, mode="down")

draw_macro_schedule()

# =========================
# 새로고침
# =========================
if st.button("새로고침"):
    st.cache_data.clear()
    st.rerun()

st.caption("데이터: Yahoo Finance / Naver Finance / Hankyung / FearGreed / Trading Economics")
