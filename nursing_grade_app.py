import streamlit as st
import pandas as pd
from datetime import date
import calendar

# ──────────────────────────────────────────────
# 페이지 기본 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="일반병동 간호관리료 등급 산정",
    page_icon="🏥",
    layout="wide",
)

# ──────────────────────────────────────────────
# CSS 스타일
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* ── 화면 스타일 ── */
    .main-title {
        font-size: 24px; font-weight: 800; color: #1a3a6b;
        border-bottom: 3px solid #1a3a6b; padding-bottom: 10px; margin-bottom: 16px;
        display: flex; align-items: baseline; gap: 12px;
    }
    .creator-badge {
        font-size: 13px; color: #888; font-weight: 500;
    }
    .section-title {
        font-size: 15px; font-weight: 700; color: #1a3a6b;
        background: #eef3fb; border-left: 5px solid #1a3a6b;
        padding: 7px 12px; margin: 14px 0 8px 0; border-radius: 0 6px 6px 0;
    }
    .result-card {
        background: #f0f7ff; border: 1.5px solid #aac8f0;
        border-radius: 10px; padding: 14px 20px; margin: 8px 0;
    }
    .grade-box {
        display: inline-block; font-size: 34px; font-weight: 900;
        padding: 12px 32px; border-radius: 12px; color: white; margin: 4px 0;
    }
    .grade-A { background: #5c1e91; }
    .grade-1 { background: #0d47a1; }
    .grade-2 { background: #1976d2; }
    .grade-3 { background: #2e7d32; }
    .grade-4 { background: #f57f17; }
    .grade-5 { background: #e65100; }
    .grade-6 { background: #b71c1c; }
    .kpi-label { font-size: 12px; color: #555; margin-bottom: 2px; }
    .kpi-value { font-size: 20px; font-weight: 700; color: #1a3a6b; }
    .kpi-unit  { font-size: 11px; color: #777; }
    .yellow-note {
        background: #fffde7; border: 1px solid #f9a825;
        border-radius: 6px; padding: 7px 12px; font-size: 12px; color: #5d4037;
        margin-bottom: 6px;
    }
    .footer {
        font-size: 13px; color: #555; text-align: center;
        margin-top: 30px; border-top: 1px solid #ddd; padding-top: 12px;
    }

    /* ── 인쇄 전용 스타일 ── */
    @media print {
        /* Streamlit UI 요소 숨기기 */
        header, footer,
        [data-testid="stToolbar"],
        [data-testid="stSidebar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .stButton > button,
        .stDownloadButton { display: none !important; }

        /* 페이지 설정: A4 가로 */
        @page { size: A4 landscape; margin: 8mm; }

        html, body { margin: 0 !important; padding: 0 !important; }

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] { padding: 0 !important; }

        [data-testid="block-container"] {
            padding: 6px 10px !important;
            max-width: 100% !important;
            width: 100% !important;
        }

        /* 전체 폰트 축소 */
        * { font-size: 9px !important; line-height: 1.3 !important; }

        /* 제목 */
        .main-title  { font-size: 13px !important; padding-bottom: 4px !important; margin-bottom: 6px !important; }
        .creator-badge { font-size: 10px !important; }
        .section-title { font-size: 10px !important; padding: 4px 8px !important; margin: 6px 0 4px 0 !important; }

        /* KPI 카드 */
        .kpi-value { font-size: 12px !important; }
        .kpi-label { font-size: 9px !important; }
        .result-card { padding: 6px 10px !important; margin: 4px 0 !important; }

        /* 등급 박스 */
        .grade-box { font-size: 18px !important; padding: 6px 16px !important; }

        /* 노트 */
        .yellow-note { padding: 4px 8px !important; font-size: 9px !important; margin-bottom: 3px !important; }

        /* 테이블 */
        table, th, td { font-size: 9px !important; padding: 2px 4px !important; }

        /* 컬럼 레이아웃 유지 */
        [data-testid="column"] { break-inside: avoid; }

        /* Streamlit 공백 요소 최소화 */
        .stMarkdown, .element-container { margin: 0 !important; padding: 0 !important; }
        hr { margin: 4px 0 !important; }

        /* footer */
        .footer { margin-top: 10px !important; padding-top: 6px !important; font-size: 10px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 유틸 함수
# ──────────────────────────────────────────────
QUARTER_RANGES = {
    "1분기 (12/15 ~ 3/14)": {"month_start": 12, "day_start": 15, "month_end": 3,  "day_end": 14},
    "2분기 (3/15 ~ 6/14)":  {"month_start": 3,  "day_start": 15, "month_end": 6,  "day_end": 14},
    "3분기 (6/15 ~ 9/14)":  {"month_start": 6,  "day_start": 15, "month_end": 9,  "day_end": 14},
    "4분기 (9/15 ~ 12/14)": {"month_start": 9,  "day_start": 15, "month_end": 12, "day_end": 14},
}

def get_quarter_dates(year, quarter_label):
    q = QUARTER_RANGES[quarter_label]
    if quarter_label.startswith("1"):
        start = date(year - 1, q["month_start"], q["day_start"])
        end   = date(year,     q["month_end"],   q["day_end"])
    else:
        start = date(year, q["month_start"], q["day_start"])
        end   = date(year, q["month_end"],   q["day_end"])
    return start, end, (end - start).days + 1

def calc_nurse_days(hire_date, status, q_start, q_end):
    if status == "퇴사":
        return 0
    total = (q_end - q_start).days + 1
    if hire_date <= q_start:
        return total
    elif hire_date <= q_end:
        return (q_end - hire_date).days + 1
    return 0

def calc_parttime_weight(weekly_hours):
    if weekly_hours >= 40: return 1.0
    elif weekly_hours >= 36: return 0.8
    elif weekly_hours >= 32: return 0.6
    else: return 0.4

def determine_grade(ratio):
    pct = ratio * 100
    if   pct < 2.0: return "A등급"
    elif pct < 2.5: return "1등급"
    elif pct < 3.0: return "2등급"
    elif pct < 3.5: return "3등급"
    elif pct < 4.0: return "4등급"
    elif pct < 6.0: return "5등급"
    else:           return "6등급"

def grade_css(grade):
    return "grade-" + grade.replace("등급", "")

def month_label(base, offset):
    m = ((base.month - 1 + offset) % 12) + 1
    y = base.year + ((base.month - 1 + offset) // 12)
    return f"{y}년 {m}월"

# ──────────────────────────────────────────────
# 세션 상태 초기화  ← 빈 칸으로 시작
# ──────────────────────────────────────────────
if "daytime_nurses" not in st.session_state:
    st.session_state.daytime_nurses = [
        {"hire_date": None, "status": "근무"},
    ]

if "night_nurses" not in st.session_state:
    st.session_state.night_nurses = [
        {"hire_date": None, "status": "근무", "weekly_hours": 40},
    ]

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown(
    '<div class="main-title">'
    '🏥 일반병동 간호관리료 등급 산정 시스템'
    '<span class="creator-badge">ㅣ 제작: 주식회사 메디엄 조정윤</span>'
    '</div>',
    unsafe_allow_html=True
)

# ──────────────────────────────────────────────
# ① 기본 정보
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">① 기본 정보</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    year = st.number_input("연도", min_value=2020, max_value=2040, value=2026, step=1)
with col2:
    quarter_label = st.selectbox("분기", list(QUARTER_RANGES.keys()), index=1)
with col3:
    beds = st.number_input("운영 병상 수", min_value=0, max_value=500, value=0, step=1,
                           placeholder="병상 수 입력")

q_start, q_end, q_days = get_quarter_dates(year, quarter_label)
st.info(f"📅 분기 기간: **{q_start}** ~ **{q_end}**  |  총 **{q_days}일**")

# ──────────────────────────────────────────────
# ② 월별 재원환자수
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">② 월별 재원환자수</div>', unsafe_allow_html=True)
st.markdown('<div class="yellow-note">🟡 <b>노란색 항목</b>: 일평균 재원환자 수는 자동 계산됩니다.</div>', unsafe_allow_html=True)

month_cols = st.columns(4)
total_patients = 0
for i in range(3):
    lbl = month_label(q_start, i)
    with month_cols[i]:
        st.markdown(f"**{lbl}**")
        pat = st.number_input("재원환자수", min_value=0, max_value=5000,
                              value=0, step=1, key=f"pat_{i}",
                              label_visibility="collapsed",
                              placeholder="환자수 입력")
        st.caption("월 재원환자수")
        total_patients += pat

with month_cols[3]:
    st.markdown("**일평균 재원환자 수** 🟡")
    avg_patients = total_patients / q_days if q_days > 0 else 0
    st.markdown(
        f'<div class="kpi-value">{avg_patients:.2f}</div>'
        f'<div class="kpi-unit">명/일 (자동계산)</div>',
        unsafe_allow_html=True
    )

# ──────────────────────────────────────────────
# ③ 주간(일반) 간호사 인력
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">③ 주간(일반) 간호사 인력</div>', unsafe_allow_html=True)

c1, c2, _ = st.columns([1, 1, 6])
with c1:
    if st.button("➕ 주간 간호사 추가"):
        st.session_state.daytime_nurses.append({"hire_date": None, "status": "근무"})
with c2:
    if st.button("➖ 마지막 행 삭제") and len(st.session_state.daytime_nurses) > 1:
        st.session_state.daytime_nurses.pop()

hc = st.columns([0.4, 2, 2, 2, 2])
hc[0].markdown("**#**"); hc[1].markdown("**입사일**"); hc[2].markdown("**상태**")
hc[3].markdown("**산정일수** 🟡"); hc[4].markdown("**환산인원** 🟡")

daytime_total = 0.0
for i, nurse in enumerate(st.session_state.daytime_nurses):
    cols = st.columns([0.4, 2, 2, 2, 2])
    cols[0].markdown(f"{i+1}")

    # 입사일: None이면 빈칸(value=None)
    hire_val = nurse["hire_date"]
    hire = cols[1].date_input(
        "입사일", value=hire_val, key=f"d_hire_{i}",
        label_visibility="collapsed"
    )

    status = cols[2].selectbox(
        "상태", ["근무", "퇴사"],
        index=0 if nurse["status"] == "근무" else 1,
        key=f"d_status_{i}", label_visibility="collapsed"
    )

    if hire is not None:
        days_worked = calc_nurse_days(hire, status, q_start, q_end)
        weight = days_worked / q_days if (status != "퇴사" and q_days > 0) else 0.0
        cols[3].markdown(f'<div style="padding-top:8px;color:#1565c0;font-weight:600">{days_worked}일</div>', unsafe_allow_html=True)
        cols[4].markdown(f'<div style="padding-top:8px;color:#1565c0;font-weight:600">{weight:.2f}명</div>', unsafe_allow_html=True)
    else:
        weight = 0.0
        cols[3].markdown('<div style="padding-top:8px;color:#bbb">-</div>', unsafe_allow_html=True)
        cols[4].markdown('<div style="padding-top:8px;color:#bbb">-</div>', unsafe_allow_html=True)

    daytime_total += weight
    st.session_state.daytime_nurses[i] = {"hire_date": hire, "status": status}

st.markdown(
    f'<div class="result-card">📊 <b>주간 간호사 3개월 평균 (환산합계)</b>: '
    f'<span class="kpi-value">{daytime_total:.2f}명</span></div>',
    unsafe_allow_html=True
)

# ──────────────────────────────────────────────
# ④ 야간전담 간호사 인력
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">④ 야간전담 간호사 인력</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="yellow-note">🟡 단시간근무자 가중치 자동 적용: '
    '주40h↑=1.0 / 주36~40h=0.8 / 주32~36h=0.6 / 주32h↓=0.4</div>',
    unsafe_allow_html=True
)

c3, c4, _ = st.columns([1, 1, 6])
with c3:
    if st.button("➕ 야간 간호사 추가"):
        st.session_state.night_nurses.append({"hire_date": None, "status": "근무", "weekly_hours": 40})
with c4:
    if st.button("➖ 마지막 행 삭제 ", key="del_night") and len(st.session_state.night_nurses) > 1:
        st.session_state.night_nurses.pop()

nh = st.columns([0.4, 2, 2, 2, 2, 2])
nh[0].markdown("**#**"); nh[1].markdown("**입사일**"); nh[2].markdown("**상태**")
nh[3].markdown("**근무시간**"); nh[4].markdown("**산정일수** 🟡"); nh[5].markdown("**환산인원** 🟡")

night_total = 0.0
for i, nurse in enumerate(st.session_state.night_nurses):
    cols = st.columns([0.4, 2, 2, 2, 2, 2])
    cols[0].markdown(f"{i+1}")

    hire_val = nurse["hire_date"]
    hire = cols[1].date_input(
        "입사일", value=hire_val, key=f"n_hire_{i}",
        label_visibility="collapsed"
    )

    status_opts = ["근무", "단시간근무", "퇴사"]
    sidx = status_opts.index(nurse["status"]) if nurse["status"] in status_opts else 0
    status = cols[2].selectbox("상태", status_opts, index=sidx,
                               key=f"n_status_{i}", label_visibility="collapsed")

    weekly_h = cols[3].number_input(
        "근무시간(h)", min_value=0, max_value=60,
        value=int(nurse.get("weekly_hours", 40)), step=1,
        key=f"n_hours_{i}", label_visibility="collapsed",
        disabled=(status != "단시간근무")
    )

    if hire is not None:
        days_worked = calc_nurse_days(hire, status, q_start, q_end)
        if status == "퇴사":
            weight = 0.0
            eff_display = "0일"
        elif status == "단시간근무":
            pw = calc_parttime_weight(weekly_h)
            weight = (days_worked / q_days) * pw if q_days > 0 else 0.0
            eff = days_worked * pw
            eff_display = f"{days_worked}일 × {pw} = {eff:.2f}일"
        else:
            weight = days_worked / q_days if q_days > 0 else 0.0
            eff_display = f"{days_worked}일"
        cols[4].markdown(f'<div style="padding-top:8px;color:#6a1b9a;font-weight:600;font-size:12px">{eff_display}</div>', unsafe_allow_html=True)
        cols[5].markdown(f'<div style="padding-top:8px;color:#6a1b9a;font-weight:600">{weight:.2f}명</div>', unsafe_allow_html=True)
    else:
        weight = 0.0
        cols[4].markdown('<div style="padding-top:8px;color:#bbb">-</div>', unsafe_allow_html=True)
        cols[5].markdown('<div style="padding-top:8px;color:#bbb">-</div>', unsafe_allow_html=True)

    night_total += weight
    st.session_state.night_nurses[i] = {"hire_date": hire, "status": status, "weekly_hours": weekly_h}

st.markdown(
    f'<div class="result-card">📊 <b>야간전담 간호사 3개월 평균 (환산합계)</b>: '
    f'<span class="kpi-value" style="color:#6a1b9a">{night_total:.2f}명</span></div>',
    unsafe_allow_html=True
)

# ──────────────────────────────────────────────
# ⑤ 등급 산정 결과 보고서
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">⑤ 등급 산정 결과 보고서</div>', unsafe_allow_html=True)
st.markdown('<div class="yellow-note">🟡 아래 항목은 모두 자동 계산됩니다.</div>', unsafe_allow_html=True)

total_nurses  = daytime_total + night_total
night_ratio   = (night_total / total_nurses * 100) if total_nurses > 0 else 0
patient_ratio = (avg_patients / total_nurses) if total_nurses > 0 else 0
grade         = determine_grade(patient_ratio / 100)

# KPI 카드
k1, k2, k3, k4, k5, k6 = st.columns(6)
def kpi(col, label, value, unit=""):
    col.markdown(
        f'<div class="result-card" style="text-align:center">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-unit">{unit}</div></div>',
        unsafe_allow_html=True
    )

kpi(k1, "🏥 운영 병상 수",         f"{beds}",                   "병상")
kpi(k2, "👥 일평균 재원환자 수",    f"{avg_patients:.2f}",       "명/일")
kpi(k3, "👩‍⚕️ 3개월 평균 간호사 수", f"{total_nurses:.2f}",        "명")
kpi(k4, "🌙 야간전담 간호사 수",    f"{night_total:.2f}",        "명")
kpi(k5, "📊 야간전담 간호사 비율",  f"{night_ratio:.2f}",        "%")
kpi(k6, "📐 환자대비 간호사수",     f"{patient_ratio:.2f}",      "(환자/간호사)")

# 등급 표시
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; margin:14px 0;">
    <div style="font-size:16px; color:#555; margin-bottom:6px;">산정 등급</div>
    <span class="grade-box {grade_css(grade)}">{grade}</span>
    <div style="font-size:13px; color:#777; margin-top:8px;">
        환자대비 간호사수: <b>{patient_ratio:.2f} ({patient_ratio:.2f}%)</b>
    </div>
</div>
""", unsafe_allow_html=True)

# 등급 기준표
st.markdown("---")
st.markdown("#### 📋 등급 기준표")
grade_list = ["A등급","1등급","2등급","3등급","4등급","5등급","6등급"]
grade_table = pd.DataFrame({
    "등급": grade_list,
    "환자대비 간호사수 기준": [
        "2.0 미만", "2.0 이상 ~ 2.5 미만", "2.5 이상 ~ 3.0 미만",
        "3.0 이상 ~ 3.5 미만", "3.5 이상 ~ 4.0 미만",
        "4.0 이상 ~ 6.0 미만", "6.0 이상"
    ],
    "현재": ["✅" if g == grade else "" for g in grade_list],
})
st.table(grade_table.set_index("등급"))

# 상세 계산 내역
with st.expander("🔍 상세 계산 내역 보기"):
    st.markdown(f"""
| 항목 | 계산식 | 결과 |
|------|--------|------|
| 분기 일수 | {q_start} ~ {q_end} | **{q_days}일** |
| 총 재원환자수 | {total_patients}명 (3개월 합계) | |
| 일평균 재원환자수 | {total_patients} ÷ {q_days}일 | **{avg_patients:.2f}명** |
| 일반병동 간호사수 [주간간호사 + 야간전담간호사] | 각 간호사 근무일수 ÷ {q_days}일 합계 | **{daytime_total:.2f}명** |
| 야간전담 간호사 환산 | 근무일수 ÷ {q_days}일 × 가중치 합계 | **{night_total:.2f}명** |
| 3개월 평균 전체 간호사 수 | 일반병동 간호사 + 야간전담 | **{total_nurses:.2f}명** |
| 야간전담 간호사 비율 | {night_total:.2f} ÷ {total_nurses:.2f} × 100 | **{night_ratio:.2f}%** |
| 환자대비 간호사수 | {avg_patients:.2f} ÷ {total_nurses:.2f} | **{patient_ratio:.2f} ({patient_ratio:.2f}%)** |
| **산정 등급** | | **{grade}** |
""")

# ──────────────────────────────────────────────
# 하단 푸터
# ──────────────────────────────────────────────
st.markdown(
    '<div class="footer">'
    '일반병동 간호관리료 등급 산정 시스템<br>'
    '<b>제작: 주식회사 메디엄 조정윤</b>'
    '</div>',
    unsafe_allow_html=True
)
