"""OpenDART 연결 재무제표를 연간·반기·분기 단위로 정리하고 주요 재무비율을 계산한다."""
from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FLOW_FIELDS = {
    "revenue", "operating_income", "profit_before_tax", "net_income",
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
    "interest_expense", "capex",
}

PEER_FIRMS = [
    {"name": "씨젠", "ticker": "096530", "market": "KOSDAQ", "focus": "분자진단·PCR", "why": "감염성 질환 중심 체외진단에서 비교 가능한 국내 상장사", "url": "https://www.seegene.com/"},
    {"name": "바디텍메드", "ticker": "206640", "market": "KOSDAQ", "focus": "현장진단(POCT)·면역진단", "why": "현장진단 플랫폼과 진단 카트리지 사업이 직접 비교 가능", "url": "https://www.boditech.co.kr/"},
    {"name": "수젠텍", "ticker": "253840", "market": "KOSDAQ", "focus": "면역진단·신속검사", "why": "체외진단 시약 및 신속진단 영역의 국내 비교기업", "url": "https://www.sugentech.com/"},
    {"name": "휴마시스", "ticker": "205470", "market": "KOSDAQ", "focus": "현장진단·자가검사", "why": "POCT 및 자가진단 제품군에서 유사성이 높은 국내 상장사", "url": "https://www.humasis.com/kr/"},
    {"name": "피씨엘", "ticker": "241820", "market": "KOSDAQ", "focus": "체외진단·다중검사", "why": "체외진단 검사 플랫폼과 시약 사업을 영위하는 국내 상장사", "url": "https://www.pcl.co.kr/"},
]

def to_number(value: str | None) -> float | None:
    if value is None:
        return None
    s = value.strip().replace(",", "")
    if s in {"", "-"}:
        return None
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return None

def load_rows() -> list[dict]:
    path = ROOT / "data" / "financial_summary.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = []
        for raw in csv.DictReader(f):
            row = {}
            for k, v in raw.items():
                if k in {"year", "period_order"}:
                    row[k] = int(v)
                elif k in {"report_code", "report_name"}:
                    row[k] = v
                else:
                    row[k] = to_number(v)
            rows.append(row)
    return sorted(rows, key=lambda r: (r["year"], r["period_order"]))

def sub(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else a - b

def ratio(a: float | None, b: float | None) -> float | None:
    return None if a is None or b in (None, 0) else a / b * 100

def average(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else (a + b) / 2

def period_days(year: int, category: str, order: int) -> int:
    if category == "annual":
        return (date(year + 1, 1, 1) - date(year, 1, 1)).days
    if category == "half":
        return (date(year, 7, 1) - date(year, 1, 1)).days
    starts = {1: date(year, 1, 1), 2: date(year, 4, 1), 3: date(year, 7, 1), 4: date(year, 10, 1)}
    ends = {1: date(year, 4, 1), 2: date(year, 7, 1), 3: date(year, 10, 1), 4: date(year + 1, 1, 1)}
    return (ends[order] - starts[order]).days

def make_quarterly(rows: list[dict]) -> list[dict]:
    by_year = {(r["year"], r["report_code"]): r for r in rows}
    out: list[dict] = []
    for year in sorted({r["year"] for r in rows}):
        q1 = by_year.get((year, "11013"))
        h1 = by_year.get((year, "11012"))
        q3 = by_year.get((year, "11014"))
        fy = by_year.get((year, "11011"))
        if q1:
            row = dict(q1); row["report_code"] = "Q1"; row["report_name"] = "1Q"; row["period_order"] = 1; row["period_label"] = f"{year} Q1"; out.append(row)
        if h1 and q1:
            row = dict(h1); row["report_code"] = "Q2"; row["report_name"] = "2Q"; row["period_order"] = 2
            for field in FLOW_FIELDS: row[field] = sub(h1.get(field), q1.get(field))
            row["period_label"] = f"{year} Q2"; out.append(row)
        if q3 and h1:
            row = dict(q3); row["report_code"] = "Q3"; row["report_name"] = "3Q"; row["period_order"] = 3
            for field in FLOW_FIELDS: row[field] = sub(q3.get(field), h1.get(field))
            row["period_label"] = f"{year} Q3"; out.append(row)
        if fy and q3:
            row = dict(fy); row["report_code"] = "Q4"; row["report_name"] = "4Q"; row["period_order"] = 4
            for field in FLOW_FIELDS: row[field] = sub(fy.get(field), q3.get(field))
            row["period_label"] = f"{year} Q4"; out.append(row)
    return sorted(out, key=lambda r: (r["year"], r["period_order"]))

def calc_ratios(rows: list[dict], category: str) -> list[dict]:
    rows = sorted(rows, key=lambda r: (r["year"], r["period_order"]))
    prior_same_period: dict[int, dict] = {}
    previous: dict | None = None
    out: list[dict] = []
    for r in rows:
        order = r["period_order"]
        same = prior_same_period.get(order)
        days = period_days(r["year"], category, order)
        avg_assets = average(r["total_assets"], previous.get("total_assets") if previous else None)
        avg_equity = average(r["total_equity"], previous.get("total_equity") if previous else None)
        avg_receivable = average(r["accounts_receivable"], previous.get("accounts_receivable") if previous else None)
        out.append({
            "year": r["year"], "report_code": r["report_code"], "report_name": r["report_name"],
            "period_order": order, "period_label": r.get("period_label"),
            "revenue_growth_pct": ratio(r["revenue"] - (same["revenue"] if same and same["revenue"] is not None else 0), same["revenue"] if same else None),
            "operating_margin_pct": ratio(r["operating_income"], r["revenue"]),
            "net_margin_pct": ratio(r["net_income"], r["revenue"]),
            "current_ratio_pct": ratio(r["current_assets"], r["current_liabilities"]),
            "debt_to_equity_pct": ratio(r["total_liabilities"], r["total_equity"]),
            "equity_ratio_pct": ratio(r["total_equity"], r["total_assets"]),
            "roa_pct": ratio(r["net_income"], avg_assets),
            "roe_pct": ratio(r["net_income"], avg_equity),
            "cfo_conversion_pct": ratio(r["operating_cash_flow"], r["net_income"]),
            "dso_days": None if avg_receivable is None or not r["revenue"] else avg_receivable / r["revenue"] * days,
            "free_cash_flow": None if r["capex"] is None or r["operating_cash_flow"] is None else r["operating_cash_flow"] - abs(r["capex"]),
        })
        previous = r
        prior_same_period[order] = r
    return out

def merge(financials: list[dict], ratios: list[dict]) -> list[dict]:
    lookup = {(r["year"], r["report_code"], r["period_order"]): r for r in ratios}
    return [{**f, **lookup.get((f["year"], f["report_code"], f["period_order"]), {})} for f in financials]

def main() -> None:
    rows = load_rows()
    annual_fin = [r for r in rows if r["report_code"] == "11011"]
    half_fin = [r for r in rows if r["report_code"] == "11012"]
    quarter_fin = make_quarterly(rows)
    annual = merge(annual_fin, calc_ratios(annual_fin, "annual"))
    half = merge(half_fin, calc_ratios(half_fin, "half"))
    quarterly = merge(quarter_fin, calc_ratios(quarter_fin, "quarter"))
    years = sorted({r["year"] for r in rows})
    dashboard = {
        "company": "에스디바이오센서",
        "company_en": "SD BIOSENSOR INC.",
        "stock_code": "137310",
        "collection_start_year": 2010,
        "coverage": "2010년부터 현재까지 OpenDART 수집을 시도하며, 연결 재무제표가 반환된 기간을 표시",
        "basis": "연결 기준. 금액 단위: 원. 2Q·3Q·4Q는 DART 누적값에서 직전 누적값을 차감한 분기 단독 실적.",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": {"provider": "OpenDART 단일회사 재무제표 API", "corp_code": "00854997", "dart_company_info": "https://englishdart.fss.or.kr/dsbc001/selectPopup.ax?selectKey=00854997"},
        "data_availability": {"first_available_year": min(years) if years else None, "available_years": years, "missing_or_unavailable_years_since_2010": [y for y in range(2010, date.today().year + 1) if y not in years]},
        "financials": rows,
        "ratios": calc_ratios(rows, "annual"),
        "annual_financials": annual_fin,
        "annual_ratios": calc_ratios(annual_fin, "annual"),
        "half_year_financials": half_fin,
        "half_year_ratios": calc_ratios(half_fin, "half"),
        "quarterly_financials": quarter_fin,
        "quarterly_ratios": calc_ratios(quarter_fin, "quarter"),
        "tables": {"annual": annual, "half_year": half, "quarterly": quarterly},
        "peer_firms": PEER_FIRMS,
        "notes": [
            "분기·반기 손익 및 현금흐름은 DART 원자료가 누적 기준이므로 분기 단독 실적은 직전 누적값 차감 방식으로 산출합니다.",
            "ROA·ROE·DSO는 직전 기간말과 현재 기간말의 평균 잔액을 사용합니다.",
            "피어는 국내 상장 체외진단·현장진단 사업의 유사성을 기준으로 한 비교군이며 직접 경쟁관계를 의미하지 않습니다."
        ]
    }
    (ROOT / "data/dashboard.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    ratios_all = calc_ratios(annual_fin, "annual") + calc_ratios(half_fin, "half") + calc_ratios(quarter_fin, "quarter")
    with (ROOT / "data/ratios.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ratios_all[0].keys())
        writer.writeheader(); writer.writerows(ratios_all)
    print(f"분석 완료: annual={len(annual)}, half_year={len(half)}, quarterly={len(quarterly)}")

if __name__ == "__main__":
    main()
