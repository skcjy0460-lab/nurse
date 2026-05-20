import streamlit as st
import pandas as pd
from datetime import date, timedelta
import math

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
    .main-title {
        font-size: 26px; font-weight: 800; color: #1a3a6b;
        border-bottom: 3px solid #1a3a6b; padding-bottom: 10px; margin-bottom: 20px;
    }
    .section-title {
        font-size: 17px; font-weight: 700; color: #1a3a6b;
        background: #eef3fb; border-left: 5px solid #1a3a6b;
        padding: 8px 14px; margin: 18px 0 10px 0; border-radius: 0 6px 6px 0;
    }
    .result-card {
        background: #f0f7ff; border: 1.5px solid #aac8f0;
        border-radius: 10px; padding: 18px 24px; margin: 10px 0;
    }
    .grade-box {
        display: inline-block;
        font-size: 36px; font-weight: 900;
        padding: 14px 36px; border-radius: 12px;
        color: white; margin: 6px 0;
    }
    .grade-A  { background: #5c1e91; }
    .grade-1  { background: #0d47a1; }
    .grade-2  { background: #1976d2; }
    .grade-3  { background: #2e7d32; }
    .grade-4  { background: #f57f17; }
    .grade-5  { background: #e65100; }
    .grade-6  { background: #b71c1c; }
    .kpi-label { font-size: 13px; color: #555; margin-bottom: 2px; }
    .kpi-value { font-size: 22px; font-weight: 700; color: #1a3a6b; }
    .kpi-unit  { font-size: 12px; color: #777; }
    .yellow-note { background: #fffde7; border: 1px solid #f9a825;
        border-radius: 6px; padding: 8px 14px; font-size: 13px; color: #5d4037; }
    .nurse-table th { background: #1a3a6b !important; color: white !important; }
    .footer { font-size: 12px; color: #aaa; text-align: center; margin-top: 40px; }
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

def get_quarter_dates(year: int, quarter_label: str):
    """분기 라벨로 시작일/종료일 반환"""
    q = QUARTER_RANGES[quarter_label]
    if quarter_label.startswith("1"):  # 12/15 ~ 다음해 3/14
        start = date(year - 1, q["month_start"], q["day_start"])
        end   = date(year,     q["month_end"],   q["day_end"])
    else:
        start = date(year, q["month_start"], q["day_start"])
        end   = date(year, q["month_end"],   q["day_end"])
    days = (end - start).days + 1
    return start, end, days

def calc_nurse_days(hire_date: date, status: str, quarter_start: date, quarter_end: date):
    """근무 간호사 실 근무일수 계산 (최대 분기 일수)"""
    if status == "퇴사":
        return 0
    total_days = (quarter_end - quarter_start).days + 1
    if hire_date <= quarter_start:
        return total_days
    elif hire_date <= quarter_end:
        return (quarter_end - hire_date).days + 1
    else:
        return 0

def calc_parttime_weight(weekly_hours: float):
    """단시간 야간 간호사 가중치"""
    if weekly_hours >= 40:
        return 1.0
    elif weekly_hours >= 36:
        return 0.8
    elif weekly_hours >= 32:
        return 0.6
    else:
        return 0.4

def determine_grade(ratio: float):
    """환자대비 간호사 비율(소수)로 등급 결정"""
    pct = ratio * 100
    if pct < 2.0:
        return "A등급"
    elif pct < 2.5:
        return "1등급"
    elif pct < 3.0:
        return "2등급"
    elif pct < 3.5:
        return "3등급"
    elif pct < 4.0:
        return "4등급"
    elif pct < 6.0:
        return "5등급"
    else:
        return "6등급"

def grade_css_class(grade: str):
    return "grade-" + grade.replace("등급", "")

# ──────────────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────────────
if "daytime_nurses" not in st.session_state:
    st.session_state.daytime_nurses = [
        {"hire_date": date(2024, 10, 28), "status": "근무"},
        {"hire_date": date(2025, 11,  8), "status": "근무"},
        {"hire_date": date(2025, 10, 12), "status": "근무"},
        {"hire_date": date(2025,  8,  4), "status": "근무"},
        {"hire_date": date(2026,  2, 10), "status": "근무"},
        {"hire_date": date(2024,  9,  7), "status": "근무"},
        {"hire_date": date(2026,  3, 23), "status": "근무"},
        {"hire_date": date(2026,  4,  6), "status": "근무"},
        {"hire_date": date(2026,  4,  6), "status": "근무"},
        {"hire_date": date(2026,  4,  6), "status": "근무"},
    ]

if "night_nurses" not in st.session_state:
    st.session_state.night_nurses = [
        {"hire_date": date(2025, 11, 29), "status": "근무",    "weekly_hours": 40},
        {"hire_date": date(2025, 10, 30), "status": "단시간근무","weekly_hours": 36},
        {"hire_date": date(2025,  9, 30), "status": "근무",    "weekly_hours": 40},
        {"hire_date": date(2026,  4, 30), "status": "단시간근무","weekly_hours": 32},
        {"hire_date": date(2026,  2,  4), "status": "퇴사",    "weekly_hours": 40},
    ]

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">🏥 일반병동 간호관리료 등급 산정 시스템</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# ① 기본 정보 입력
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">① 기본 정보</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    year = st.number_input("연도", min_value=2020, max_value=2040, value=2026, step=1)
with col2:
    quarter_label = st.selectbox("분기", list(QUARTER_RANGES.keys()), index=1)
with col3:
    beds = st.number_input("운영 병상 수", min_value=1, max_value=500, value=52, step=1)

q_start, q_end, q_days = get_quarter_dates(year, quarter_label)
st.info(f"📅 분기 기간: **{q_start}** ~ **{q_end}**  |  총 **{q_days}일**")

# ──────────────────────────────────────────────
# ② 월별 재원환자수 입력
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">② 월별 재원환자수</div>', unsafe_allow_html=True)
st.markdown('<div class="yellow-note">🟡 <b>노란색 항목</b>: 일평균 재원환자 수는 자동 계산됩니다.</div>', unsafe_allow_html=True)

# 분기에 맞는 3개월 라벨 생성
def month_label(base: date, offset: int):
    m = ((base.month - 1 + offset) % 12) + 1
    y = base.year + ((base.month - 1 + offset) // 12)
    return f"{y}년 {m}월"

month_cols = st.columns(4)
month_data = []
total_patients = 0
for i in range(3):
    lbl = month_label(q_start, i)
    # 해당 월의 일수 추정 (간단히 28~31)
    m = ((q_start.month - 1 + i) % 12) + 1
    y = q_start.year + ((q_start.month - 1 + i) // 12)
    import calendar
    days_in_month = calendar.monthrange(y, m)[1]
    with month_cols[i]:
        st.markdown(f"**{lbl}**")
        pat = st.number_input(f"재원환자수 (명)", min_value=0, max_value=5000,
                              value=[994, 948, 758][i], step=1, key=f"pat_{i}",
                              label_visibility="collapsed")
        st.caption(f"월 재원환자수")
        month_data.append({"label": lbl, "patients": pat, "days": days_in_month})
        total_patients += pat

with month_cols[3]:
    st.markdown("**일평균 재원환자 수** 🟡")
    avg_patients = total_patients / q_days
    st.markdown(f'<div class="kpi-value">{avg_patients:.2f}</div><div class="kpi-unit">명/일 (자동계산)</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# ③ 주간 간호사 입력
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">③ 주간(일반) 간호사 인력</div>', unsafe_allow_html=True)

# 추가/삭제 버튼
c1, c2, _ = st.columns([1, 1, 6])
with c1:
    if st.button("➕ 주간 간호사 추가"):
        st.session_state.daytime_nurses.append({"hire_date": date.today(), "status": "근무"})
with c2:
    if st.button("➖ 마지막 행 삭제") and len(st.session_state.daytime_nurses) > 1:
        st.session_state.daytime_nurses.pop()

header_cols = st.columns([0.4, 2, 2, 2, 2])
header_cols[0].markdown("**#**")
header_cols[1].markdown("**입사일**")
header_cols[2].markdown("**상태**")
header_cols[3].markdown("**산정일수** 🟡")
header_cols[4].markdown("**환산인원** 🟡")

daytime_total_weight = 0.0
for i, nurse in enumerate(st.session_state.daytime_nurses):
    cols = st.columns([0.4, 2, 2, 2, 2])
    cols[0].markdown(f"{i+1}")
    hire = cols[1].date_input("입사일", value=nurse["hire_date"], key=f"d_hire_{i}",
                              label_visibility="collapsed")
    status = cols[2].selectbox("상태", ["근무", "퇴사"], 
                               index=0 if nurse["status"] == "근무" else 1,
                               key=f"d_status_{i}", label_visibility="collapsed")
    days_worked = calc_nurse_days(hire, status, q_start, q_end)
    weight = days_worked / q_days if status != "퇴사" else 0.0
    cols[3].markdown(f'<div style="padding-top:8px;color:#1565c0;font-weight:600">{days_worked}일</div>', unsafe_allow_html=True)
    cols[4].markdown(f'<div style="padding-top:8px;color:#1565c0;font-weight:600">{weight:.2f}명</div>', unsafe_allow_html=True)
    daytime_total_weight += weight
    st.session_state.daytime_nurses[i] = {"hire_date": hire, "status": status}

st.markdown(f'<div class="result-card">📊 <b>주간 간호사 3개월 평균 (환산합계)</b>: <span class="kpi-value">{daytime_total_weight:.2f}명</span></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# ④ 야간전담 간호사 입력
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">④ 야간전담 간호사 인력</div>', unsafe_allow_html=True)
st.markdown('<div class="yellow-note">🟡 단시간근무자는 주간 근무시간에 따라 가중치 자동 적용: 40h↑=1.0 / 36~40h=0.8 / 32~36h=0.6 / 32h↓=0.4</div>', unsafe_allow_html=True)

c3, c4, _ = st.columns([1, 1, 6])
with c3:
    if st.button("➕ 야간 간호사 추가"):
        st.session_state.night_nurses.append({"hire_date": date.today(), "status": "근무", "weekly_hours": 40})
with c4:
    if st.button("➖ 마지막 행 삭제 ", key="del_night") and len(st.session_state.night_nurses) > 1:
        st.session_state.night_nurses.pop()

n_header = st.columns([0.4, 2, 2, 2, 2, 2])
n_header[0].markdown("**#**")
n_header[1].markdown("**입사일**")
n_header[2].markdown("**상태**")
n_header[3].markdown("**근무시간**")
n_header[4].markdown("**산정일수** 🟡")
n_header[5].markdown("**환산인원** 🟡")

night_total_weight = 0.0
for i, nurse in enumerate(st.session_state.night_nurses):
    cols = st.columns([0.4, 2, 2, 2, 2, 2])
    cols[0].markdown(f"{i+1}")
    hire = cols[1].date_input("입사일", value=nurse["hire_date"], key=f"n_hire_{i}",
                              label_visibility="collapsed")
    status_options = ["근무", "단시간근무", "퇴사"]
    status_idx = status_options.index(nurse["status"]) if nurse["status"] in status_options else 0
    status = cols[2].selectbox("상태", status_options, index=status_idx,
                               key=f"n_status_{i}", label_visibility="collapsed")
    weekly_h = cols[3].number_input("근무시간", min_value=0, max_value=60,
                                     value=int(nurse.get("weekly_hours", 40)), step=1,
                                     key=f"n_hours_{i}", label_visibility="collapsed",
                                     disabled=(status not in ["단시간근무"]))
    days_worked = calc_nurse_days(hire, status, q_start, q_end)
    if status == "퇴사":
        weight = 0.0
        pt_weight = 0.0
        effective_days_display = "0일"
    elif status == "단시간근무":
        pt_weight = calc_parttime_weight(weekly_h)
        weight = (days_worked / q_days) * pt_weight
        effective_days = days_worked * pt_weight
        effective_days_display = f"{days_worked}일 × {pt_weight} = {effective_days:.2f}일"
    else:
        pt_weight = 1.0
        weight = days_worked / q_days
        effective_days_display = f"{days_worked}일"
    cols[4].markdown(f'<div style="padding-top:8px;color:#6a1b9a;font-weight:600;font-size:13px">{effective_days_display}</div>', unsafe_allow_html=True)
    cols[5].markdown(f'<div style="padding-top:8px;color:#6a1b9a;font-weight:600">{weight:.2f}명</div>', unsafe_allow_html=True)
    night_total_weight += weight
    st.session_state.night_nurses[i] = {"hire_date": hire, "status": status, "weekly_hours": weekly_h}

st.markdown(f'<div class="result-card">📊 <b>야간전담 간호사 3개월 평균 (환산합계)</b>: <span class="kpi-value" style="color:#6a1b9a">{night_total_weight:.2f}명</span></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# ⑤ 최종 계산 및 보고서
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">⑤ 등급 산정 결과 보고서</div>', unsafe_allow_html=True)
st.markdown('<div class="yellow-note">🟡 아래 항목은 모두 자동 계산됩니다.</div>', unsafe_allow_html=True)

total_nurses = daytime_total_weight + night_total_weight
night_ratio  = (night_total_weight / total_nurses * 100) if total_nurses > 0 else 0
patient_ratio = (avg_patients / total_nurses) if total_nurses > 0 else 0
grade = determine_grade(patient_ratio / 100)

# KPI 카드
k1, k2, k3, k4, k5, k6 = st.columns(6)
def kpi(col, label, value, unit=""):
    col.markdown(f'<div class="result-card" style="text-align:center">'
                 f'<div class="kpi-label">{label}</div>'
                 f'<div class="kpi-value">{value}</div>'
                 f'<div class="kpi-unit">{unit}</div></div>', unsafe_allow_html=True)

kpi(k1, "🏥 운영 병상 수",        f"{beds}",                    "병상")
kpi(k2, "👥 일평균 재원환자 수",   f"{avg_patients:.2f}",        "명/일")
kpi(k3, "👩‍⚕️ 3개월 평균 간호사 수", f"{total_nurses:.2f}",         "명")
kpi(k4, "🌙 야간전담 간호사 수",   f"{night_total_weight:.2f}",  "명")
kpi(k5, "📊 야간전담 간호사 비율", f"{night_ratio:.2f}",         "%")
kpi(k6, "📐 환자대비 간호사수",    f"{patient_ratio:.2f}",       "(환자/간호사)")

# 등급 표시
st.markdown("---")
gcls = grade_css_class(grade)
grade_display = grade
st.markdown(f"""
<div style="text-align:center; margin: 20px 0;">
    <div style="font-size:18px; color:#555; margin-bottom:8px;">산정 등급</div>
    <span class="grade-box {gcls}">{grade_display}</span>
    <div style="font-size:14px; color:#777; margin-top:10px;">
        환자대비 간호사수: <b>{patient_ratio:.2f} ({patient_ratio:.2f}%)</b>
    </div>
</div>
""", unsafe_allow_html=True)

# 등급 기준표
st.markdown("---")
st.markdown("#### 📋 등급 기준표")
grade_table = pd.DataFrame({
    "등급":         ["A등급", "1등급", "2등급", "3등급", "4등급", "5등급", "6등급"],
    "환자대비 간호사수 기준": [
        "2.0 미만", "2.0 이상 ~ 2.5 미만", "2.5 이상 ~ 3.0 미만",
        "3.0 이상 ~ 3.5 미만", "3.5 이상 ~ 4.0 미만",
        "4.0 이상 ~ 6.0 미만", "6.0 이상"
    ],
    "현재":         ["✅" if g == grade else "" for g in ["A등급","1등급","2등급","3등급","4등급","5등급","6등급"]],
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
| 일반병동 간호사수 [주간간호사 + 야간전담간호사] | 각 간호사 근무일수 ÷ {q_days}일 합계 | **{daytime_total_weight:.2f}명** |
| 야간전담 간호사 환산 | 근무일수 ÷ {q_days}일 × 가중치 합계 | **{night_total_weight:.2f}명** |
| 3개월 평균 전체 간호사 수 | 일반병동 간호사 + 야간전담 | **{total_nurses:.2f}명** |
| 야간전담 간호사 비율 | {night_total_weight:.2f} ÷ {total_nurses:.2f} × 100 | **{night_ratio:.2f}%** |
| 환자대비 간호사수 | {avg_patients:.2f} ÷ {total_nurses:.2f} | **{patient_ratio:.2f} ({patient_ratio:.2f}%)** |
| **산정 등급** | | **{grade}** |
""")

st.markdown('<div class="footer">병원 개원 및 경영 컨설팅 | 일반병동 간호관리료 등급 산정 시스템</div>', unsafe_allow_html=True)
