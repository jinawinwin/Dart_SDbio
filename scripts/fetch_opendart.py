"""OpenDART에서 에스디바이오센서의 연간·분기·반기 연결 재무제표를 수집한다."""
from __future__ import annotations
import argparse, csv, json, os
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]; API="https://opendart.fss.or.kr/api"; CORP_CODE="00854997"
COMPANY_RSS="https://dart.fss.or.kr/api/companyRSS.xml?crpCd=00854997"
REPORTS={"11013":("1분기보고서",1),"11012":("반기보고서",2),"11014":("3분기보고서",3),"11011":("사업보고서",4)}
ACCOUNTS={"revenue":{"매출액","수익(매출액)","영업수익"},"operating_income":{"영업이익","영업이익(손실)"},"profit_before_tax":{"법인세비용차감전순이익","법인세비용차감전순이익(손실)"},"net_income":{"당기순이익","당기순이익(손실)"},"current_assets":{"유동자산"},"noncurrent_assets":{"비유동자산"},"total_assets":{"자산총계"},"current_liabilities":{"유동부채"},"noncurrent_liabilities":{"비유동부채"},"total_liabilities":{"부채총계"},"total_equity":{"자본총계"},"operating_cash_flow":{"영업활동으로인한현금흐름","영업활동현금흐름"},"investing_cash_flow":{"투자활동으로인한현금흐름","투자활동현금흐름"},"financing_cash_flow":{"재무활동으로인한현금흐름","재무활동현금흐름"},"cash_and_cash_equivalents":{"현금및현금성자산"},"accounts_receivable":{"매출채권","매출채권및기타채권"},"inventory":{"재고자산"},"interest_expense":{"이자비용"},"capex":{"유형자산의취득","유형자산취득","유형자산의취득으로인한현금유출액"}}
ACCOUNT_IDS={
    "revenue":{"ifrs-full_Revenue","ifrs-full_RevenueFromContractsWithCustomers","dart_OperatingRevenue"},
    "operating_income":{"dart_OperatingIncomeLoss","ifrs-full_ProfitLossFromOperatingActivities"},
    "profit_before_tax":{"ifrs-full_ProfitLossBeforeTax"},
    "net_income":{"ifrs-full_ProfitLoss","ifrs-full_ProfitLossAttributableToOwnersOfParent"},
    "current_assets":{"ifrs-full_CurrentAssets"},"noncurrent_assets":{"ifrs-full_NoncurrentAssets"},"total_assets":{"ifrs-full_Assets"},
    "current_liabilities":{"ifrs-full_CurrentLiabilities"},"noncurrent_liabilities":{"ifrs-full_NoncurrentLiabilities"},
    "total_liabilities":{"ifrs-full_Liabilities"},"total_equity":{"ifrs-full_Equity"},
    "operating_cash_flow":{"ifrs-full_CashFlowsFromUsedInOperatingActivities"},
    "investing_cash_flow":{"ifrs-full_CashFlowsFromUsedInInvestingActivities"},
    "financing_cash_flow":{"ifrs-full_CashFlowsFromUsedInFinancingActivities"},
    "cash_and_cash_equivalents":{"ifrs-full_CashAndCashEquivalents"},"inventory":{"ifrs-full_Inventories"},
}
FIELDS=["year","report_code","report_name","period_order",*ACCOUNTS]
REQUIRED={"revenue","operating_income","net_income","current_assets","total_assets","current_liabilities","total_liabilities","total_equity","operating_cash_flow"}

def compact(s:str)->str:return "".join(s.split()).replace("(손실)","")
def load_dotenv():
    p=ROOT/".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1);os.environ.setdefault(k.strip(),v.strip().strip('"'))
def request(endpoint:str,params:dict[str,str])->dict:
    with urlopen(f"{API}/{endpoint}?{urlencode(params)}",timeout=60) as response:return json.load(response)
def amount(v:str|None)->int|None:return None if not v or v.strip() in {"-","0"} else int(v.replace(",",""))
def normalise(year:int,code:str,items:list[dict])->dict:
    name,order=REPORTS[code]; row={"year":year,"report_code":code,"report_name":name,"period_order":order,**{k:None for k in ACCOUNTS}}
    for field,labels in ACCOUNTS.items():
        # OpenDART는 회사·연도별로 한글 계정명이 달라질 수 있다.
        # IFRS 계정 ID를 함께 사용해 매출·순이익 등의 표기 차이를 흡수한다.
        names={compact(label) for label in labels}; ids=ACCOUNT_IDS.get(field,set())
        matches=[x for x in items if compact(x.get("account_nm","")) in names or x.get("account_id") in ids]
        selected=next((x for x in matches if x.get("fs_div")=="CFS"),matches[0] if matches else None)
        if selected:row[field]=amount(selected.get("thstrm_amount"))
    missing=sorted(x for x in REQUIRED if row[x] is None)
    if missing:raise RuntimeError(f"{year}년 {name} 필수 계정 누락: {', '.join(missing)}")
    return row
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--api-key");parser.add_argument("--start-year",type=int,default=2010);args=parser.parse_args();load_dotenv()
    key=args.api_key or os.environ.get("DART_API_KEY")
    if not key:raise SystemExit("DART_API_KEY가 없습니다. GitHub Actions Secrets 또는 .env에 설정하세요.")
    raw=ROOT/"data"/"raw";raw.mkdir(parents=True,exist_ok=True);rows=[]
    for year in range(args.start_year,date.today().year+1):
        for code in REPORTS:
            data=request("fnlttSinglAcntAll.json",{"crtfc_key":key,"corp_code":CORP_CODE,"bsns_year":str(year),"reprt_code":code,"fs_div":"CFS"})
            if data.get("status")!="000":continue
            (raw/f"opendart_sdbiosensor_{year}_{code}.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
            try:rows.append(normalise(year,code,data["list"]))
            except RuntimeError as err:print(f"경고: {err}. 해당 기간은 분석에서 제외합니다.")
    if len(rows)<2:raise RuntimeError("분석에 필요한 완전한 연결 재무제표가 2개 기간보다 적습니다.")
    rows.sort(key=lambda r:(r["year"],r["period_order"]))
    with (ROOT/"data"/"financial_summary.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    disclosure=request("list.json",{"crtfc_key":key,"corp_code":CORP_CODE,"bgn_de":f"{args.start_year}0101","end_de":date.today().strftime("%Y%m%d"),"pblntf_ty":"A","page_count":"100"})
    (ROOT/"reports"/"opendart_disclosures.json").write_text(json.dumps({"rss_url":COMPANY_RSS,"reports":disclosure.get("list",[])},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"수집 완료: {len(rows)}개 기간 ({args.start_year}년~현재)")
if __name__=="__main__":main()
