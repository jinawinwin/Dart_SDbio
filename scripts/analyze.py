"""재무제표 가이드의 수익성, 유동성, 안정성, 현금흐름 지표를 계산한다."""
from __future__ import annotations
import csv, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def num(v: str) -> float | None: return float(v) if v and v.strip() else None
def pct(a: float | None, b: float | None) -> float | None: return None if a is None or b in (None, 0) else a / b * 100
def avg(a: float | None, b: float | None) -> float | None: return None if a is None or b is None else (a + b) / 2
def fmt(v: float | None) -> str: return "N/A" if v is None else f"{v:.1f}%"
def eok(v: float | None) -> str: return "N/A" if v is None else f"{v / 100_000_000:,.0f}억원"

def main() -> None:
    with (ROOT / "data/financial_summary.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = [{k: (int(v) if k == "year" else num(v)) for k, v in r.items()} for r in csv.DictReader(f)]
    if len(rows) < 2: raise SystemExit("비율 분석에는 최소 2개 연도 데이터가 필요합니다.")
    ratios=[]
    for i, r in enumerate(rows):
        p = rows[i-1] if i else None; ar=avg(r["accounts_receivable"], p["accounts_receivable"]) if p else None
        assets, equity = (avg(r["total_assets"], p["total_assets"]) if p else None), (avg(r["total_equity"], p["total_equity"]) if p else None)
        ebitda = None if r["operating_income"] is None else r["operating_income"]
        ratios.append({"year":r["year"], "revenue_growth_pct":pct(r["revenue"]-(p["revenue"] if p else 0),p["revenue"] if p else None), "operating_margin_pct":pct(r["operating_income"],r["revenue"]), "net_margin_pct":pct(r["net_income"],r["revenue"]), "current_ratio_pct":pct(r["current_assets"],r["current_liabilities"]), "debt_to_equity_pct":pct(r["total_liabilities"],r["total_equity"]), "equity_ratio_pct":pct(r["total_equity"],r["total_assets"]), "roa_pct":pct(r["net_income"],assets), "roe_pct":pct(r["net_income"],equity), "cfo_conversion_pct":pct(r["operating_cash_flow"],r["net_income"]), "dso_days":None if ar is None or not r["revenue"] else ar/r["revenue"]*365, "free_cash_flow":None if r["capex"] is None else r["operating_cash_flow"]-abs(r["capex"])})
    with (ROOT / "data/ratios.csv").open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f,fieldnames=ratios[0].keys()); w.writeheader(); w.writerows(ratios)
    dashboard={"company":"에스디바이오센서", "stock_code":"137310", "basis":"연결 기준, 단위: 원", "updated_at":datetime.now(timezone.utc).isoformat(), "source":{"provider":"OpenDART 단일회사 재무제표 API", "corp_code":"00854997", "report_code":"11011", "rss_url":"https://dart.fss.or.kr/api/companyRSS.xml?crpCd=00854997"}, "financials":rows, "ratios":ratios}
    (ROOT / "data/dashboard.json").write_text(json.dumps(dashboard,ensure_ascii=False,indent=2),encoding="utf-8")
    c, p, z=rows[-1], rows[-2], ratios[-1]
    (ROOT / "analysis").mkdir(exist_ok=True)
    (ROOT / "analysis/latest_financial_analysis.md").write_text(f"# 에스디바이오센서 {c['year']} 연결 재무 분석\n\n- 매출액: {eok(c['revenue'])}, 전년 대비 {fmt(z['revenue_growth_pct'])}\n- 영업이익률: {fmt(z['operating_margin_pct'])}; 순이익률: {fmt(z['net_margin_pct'])}\n- 유동비율: {fmt(z['current_ratio_pct'])}; 부채비율: {fmt(z['debt_to_equity_pct'])}; 자기자본비율: {fmt(z['equity_ratio_pct'])}\n- ROA: {fmt(z['roa_pct'])}; ROE: {fmt(z['roe_pct'])}; CFO 전환율: {fmt(z['cfo_conversion_pct'])}\n\nROA·ROE와 DSO는 가이드 원칙에 따라 평균 잔액을 사용합니다. CAPEX 계정이 확인된 연도만 FCF를 표시합니다. 투자 권유가 아닙니다.\n",encoding="utf-8")

if __name__ == "__main__": main()
