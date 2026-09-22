from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "financial_summary.csv"
RATIO_OUTPUT = ROOT / "data" / "ratios.csv"
REPORT_OUTPUT = ROOT / "analysis" / "2025_financial_analysis.md"
DASHBOARD_OUTPUT = ROOT / "data" / "dashboard.json"

FIELDS = {
    "revenue", "operating_income", "profit_before_tax", "net_income",
    "current_assets", "noncurrent_assets", "total_assets", "current_liabilities",
    "noncurrent_liabilities", "total_liabilities", "total_equity",
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
    "cash_and_cash_equivalents", "accounts_receivable", "inventory",
}


def number(value: str) -> float | None:
    value = value.strip()
    return float(value) if value else None


def pct(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator * 100


def won_to_100m(value: float) -> str:
    return f"{value / 100_000_000:,.0f}억원"


def fmt_pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1f}%"


def main() -> None:
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        records = []
        for row in csv.DictReader(f):
            records.append({key: (int(row[key]) if key == "year" else number(row[key])) for key in row})

    ratios: list[dict[str, float | int | None]] = []
    for index, row in enumerate(records):
        previous = records[index - 1] if index else None
        avg_assets = ((row["total_assets"] + previous["total_assets"]) / 2) if previous else None
        avg_equity = ((row["total_equity"] + previous["total_equity"]) / 2) if previous else None
        avg_receivables = (
            (row["accounts_receivable"] + previous["accounts_receivable"]) / 2
            if previous and row["accounts_receivable"] and previous["accounts_receivable"] else None
        )
        ratios.append({
            "year": row["year"],
            "revenue_growth_pct": pct(row["revenue"] - previous["revenue"], previous["revenue"]) if previous else None,
            "operating_margin_pct": pct(row["operating_income"], row["revenue"]),
            "net_margin_pct": pct(row["net_income"], row["revenue"]),
            "current_ratio_pct": pct(row["current_assets"], row["current_liabilities"]),
            "debt_to_equity_pct": pct(row["total_liabilities"], row["total_equity"]),
            "equity_ratio_pct": pct(row["total_equity"], row["total_assets"]),
            "roa_pct": pct(row["net_income"], avg_assets),
            "roe_pct": pct(row["net_income"], avg_equity),
            "cfo_conversion_pct": pct(row["operating_cash_flow"], row["net_income"]),
            "dso_days": (avg_receivables / row["revenue"] * 365) if avg_receivables else None,
        })

    RATIO_OUTPUT.parent.mkdir(exist_ok=True)
    with RATIO_OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ratios[0].keys())
        writer.writeheader()
        writer.writerows(ratios)

    DASHBOARD_OUTPUT.write_text(json.dumps({
        "company": "유한양행",
        "stock_code": "000100",
        "basis": "연결 기준, 단위: 원",
        "source": {
            "provider": "OpenDART 단일회사 재무제표 API",
            "report_code": "11011",
            "corp_code": "00145109",
            "report_url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260312004696",
        },
        "financials": records,
        "ratios": ratios,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    current = records[-1]
    prior = records[-2]
    ratio = ratios[-1]
    REPORT_OUTPUT.parent.mkdir(exist_ok=True)
    REPORT_OUTPUT.write_text(f"""# 유한양행 2025 연결 재무 분석

## 핵심 결론

- 매출은 {won_to_100m(current['revenue'])}이며 전년 대비 {fmt_pct(ratio['revenue_growth_pct'])} 성장했습니다. 영업이익은 {won_to_100m(current['operating_income'])}으로 늘어 영업이익률이 {fmt_pct(ratio['operating_margin_pct'])}가 되었습니다.
- 당기순이익은 {won_to_100m(current['net_income'])}으로 크게 증가했으나, CFO 전환율은 {fmt_pct(ratio['cfo_conversion_pct'])}입니다. 처분이익 등 비경상 항목의 영향을 분리해 확인할 필요가 있습니다.
- 유동비율은 {fmt_pct(ratio['current_ratio_pct'])}, 부채비율은 {fmt_pct(ratio['debt_to_equity_pct'])}, 자기자본비율은 {fmt_pct(ratio['equity_ratio_pct'])}로 단기 유동성과 자본완충력은 양호한 편입니다.

## 주요 수치

| 항목 | 2025 | 2024 | 변화 |
| --- | ---: | ---: | ---: |
| 매출액 | {won_to_100m(current['revenue'])} | {won_to_100m(prior['revenue'])} | {fmt_pct(ratio['revenue_growth_pct'])} |
| 영업이익 | {won_to_100m(current['operating_income'])} | {won_to_100m(prior['operating_income'])} | {pct(current['operating_income']-prior['operating_income'], prior['operating_income']):.1f}% |
| 당기순이익 | {won_to_100m(current['net_income'])} | {won_to_100m(prior['net_income'])} | {pct(current['net_income']-prior['net_income'], prior['net_income']):.1f}% |
| 영업활동현금흐름 | {won_to_100m(current['operating_cash_flow'])} | {won_to_100m(prior['operating_cash_flow'])} | {pct(current['operating_cash_flow']-prior['operating_cash_flow'], prior['operating_cash_flow']):.1f}% |
| 자산총계 | {won_to_100m(current['total_assets'])} | {won_to_100m(prior['total_assets'])} | {pct(current['total_assets']-prior['total_assets'], prior['total_assets']):.1f}% |
| 자본총계 | {won_to_100m(current['total_equity'])} | {won_to_100m(prior['total_equity'])} | {pct(current['total_equity']-prior['total_equity'], prior['total_equity']):.1f}% |

## 재무비율

| 지표 | 2025 | 해석 |
| --- | ---: | --- |
| 영업이익률 | {fmt_pct(ratio['operating_margin_pct'])} | 2024년 {fmt_pct(ratios[-2]['operating_margin_pct'])}에서 개선 |
| 순이익률 | {fmt_pct(ratio['net_margin_pct'])} | 비영업 항목 영향 가능성을 주석에서 확인 필요 |
| ROA | {fmt_pct(ratio['roa_pct'])} | 2024~2025 평균자산 기준 |
| ROE | {fmt_pct(ratio['roe_pct'])} | 2024~2025 평균자본 기준 |
| 유동비율 | {fmt_pct(ratio['current_ratio_pct'])} | 유동자산 대비 유동부채 |
| 부채비율 | {fmt_pct(ratio['debt_to_equity_pct'])} | 총부채 / 자본총계 |
| CFO 전환율 | {fmt_pct(ratio['cfo_conversion_pct'])} | 순이익의 현금 전환 정도 |
| DSO | {ratio['dso_days']:.1f}일 | 2024~2025 평균 매출채권 기준 |

## 해석 시 주의점

1. 2025년 순이익 증가는 영업이익 증가만으로 설명되지 않습니다. 사업보고서의 관계기업 투자주식·투자부동산 처분 관련 손익을 주석에서 확인해 반복 가능 이익과 구분해야 합니다.
2. CFO는 전년보다 증가했지만 순이익보다 작은 수준입니다. 매출채권, 재고자산, 지급조건 변화를 다음 분석에서 함께 점검해야 합니다.
3. FCF·ROIC는 DART 주석에서 CAPEX와 투자자본을 일관된 정의로 확정한 뒤 추가합니다. 현재 수집된 요약표만으로는 산출하지 않습니다.

## 재현성

원자료는 `data/financial_summary.csv`, 계산 결과는 `data/ratios.csv`, 계산 로직은 `scripts/analyze.py`에 있습니다. 모든 금액은 원화이며, 본 문서는 투자 권유가 아닙니다.
""", encoding="utf-8")


if __name__ == "__main__":
    main()
