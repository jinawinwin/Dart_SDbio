"""연간·분기·반기 연결 재무제표의 주요 재무비율을 계산한다."""
from __future__ import annotations
import csv,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def n(v):return float(v) if v and v.strip() else None
def pct(a,b):return None if a is None or b in (None,0) else a/b*100
def average(a,b):return None if a is None or b is None else (a+b)/2
def main():
    with (ROOT/"data/financial_summary.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=[{k:(int(v) if k in {"year","period_order"} else v if k in {"report_code","report_name"} else n(v)) for k,v in x.items()} for x in csv.DictReader(f)]
    rows.sort(key=lambda r:(r["year"],r["period_order"]));prior={};ratios=[]
    for r in rows:
        p=prior.get(r["report_code"]); assets=average(r["total_assets"],p["total_assets"]) if p else None; equity=average(r["total_equity"],p["total_equity"]) if p else None; receivable=average(r["accounts_receivable"],p["accounts_receivable"]) if p else None
        ratios.append({"year":r["year"],"report_code":r["report_code"],"report_name":r["report_name"],"period_order":r["period_order"],"revenue_growth_pct":pct(r["revenue"]-(p["revenue"] if p else 0),p["revenue"] if p else None),"operating_margin_pct":pct(r["operating_income"],r["revenue"]),"net_margin_pct":pct(r["net_income"],r["revenue"]),"current_ratio_pct":pct(r["current_assets"],r["current_liabilities"]),"debt_to_equity_pct":pct(r["total_liabilities"],r["total_equity"]),"equity_ratio_pct":pct(r["total_equity"],r["total_assets"]),"roa_pct":pct(r["net_income"],assets),"roe_pct":pct(r["net_income"],equity),"cfo_conversion_pct":pct(r["operating_cash_flow"],r["net_income"]),"dso_days":None if receivable is None or not r["revenue"] else receivable/r["revenue"]*365,"free_cash_flow":None if r["capex"] is None else r["operating_cash_flow"]-abs(r["capex"])})
        prior[r["report_code"]]=r
    with (ROOT/"data/ratios.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=ratios[0].keys());w.writeheader();w.writerows(ratios)
    annual=[r for r in rows if r["report_code"]=="11011"];annual_ratios=[r for r in ratios if r["report_code"]=="11011"]
    dashboard={"company":"에스디바이오센서","stock_code":"137310","coverage":"2010년부터 현재까지 연간·1분기·반기·3분기","basis":"연결 기준, 단위: 원. 분기·반기 손익·현금흐름은 누적 기준일 수 있음.","updated_at":datetime.now(timezone.utc).isoformat(),"source":{"provider":"OpenDART 단일회사 재무제표 API","corp_code":"00854997"},"financials":rows,"ratios":ratios,"annual_financials":annual,"annual_ratios":annual_ratios}
    (ROOT/"data/dashboard.json").write_text(json.dumps(dashboard,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"분석 완료: {len(ratios)}개 기간")
if __name__=="__main__":main()
