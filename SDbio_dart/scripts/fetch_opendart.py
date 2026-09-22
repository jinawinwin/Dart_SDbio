"""OpenDART에서 에스디바이오센서 연결 연간 재무제표와 사업보고서 목록을 수집한다."""
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://opendart.fss.or.kr/api"
CORP_CODE = "00854997"  # 에스디바이오센서 DART 고유번호
REPORT_CODE = "11011"  # 사업보고서
COMPANY_RSS = "https://dart.fss.or.kr/api/companyRSS.xml?crpCd=00854997"

# DART 표기 차이를 함께 허용한다. 값은 연결(CFS)을 우선 선택한다.
ACCOUNTS = {
    "revenue": {"매출액", "수익(매출액)", "영업수익"},
    "operating_income": {"영업이익", "영업이익(손실)"},
    "profit_before_tax": {"법인세비용차감전순이익", "법인세비용차감전순이익(손실)"},
    "net_income": {"당기순이익", "당기순이익(손실)"},
    "current_assets": {"유동자산"}, "noncurrent_assets": {"비유동자산"}, "total_assets": {"자산총계"},
    "current_liabilities": {"유동부채"}, "noncurrent_liabilities": {"비유동부채"},
    "total_liabilities": {"부채총계"}, "total_equity": {"자본총계"},
    "operating_cash_flow": {"영업활동으로인한현금흐름", "영업활동현금흐름"},
    "investing_cash_flow": {"투자활동으로인한현금흐름", "투자활동현금흐름"},
    "financing_cash_flow": {"재무활동으로인한현금흐름", "재무활동현금흐름"},
    "cash_and_cash_equivalents": {"현금및현금성자산"},
    "accounts_receivable": {"매출채권", "매출채권및기타채권"}, "inventory": {"재고자산"},
    "interest_expense": {"이자비용"},
    "capex": {"유형자산의취득", "유형자산취득", "유형자산의취득으로인한현금유출액"},
}
FIELDS = ["year", *ACCOUNTS]
REQUIRED = {"revenue", "operating_income", "net_income", "current_assets", "total_assets", "current_liabilities", "total_liabilities", "total_equity", "operating_cash_flow"}


def compact(text: str) -> str:
    return "".join(text.split()).replace("(손실)", "")


def load_dotenv() -> None:
    path = ROOT / ".env"
    if not path.exists(): return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1); os.environ.setdefault(key.strip(), value.strip().strip('"'))


def request(endpoint: str, params: dict[str, str]) -> dict:
    with urlopen(f"{API}/{endpoint}?{urlencode(params)}", timeout=60) as response:
        return json.load(response)


def as_number(value: str | None) -> int | None:
    if not value or value.strip() in {"-", "0"}: return None
    return int(value.replace(",", ""))


def normalise(year: int, items: list[dict]) -> dict[str, int | None]:
    row: dict[str, int | None] = {"year": year, **{field: None for field in ACCOUNTS}}
    for field, labels in ACCOUNTS.items():
        candidates = [x for x in items if compact(x.get("account_nm", "")) in labels]
        preferred = next((x for x in candidates if x.get("fs_div") == "CFS"), candidates[0] if candidates else None)
        if preferred: row[field] = as_number(preferred.get("thstrm_amount"))
    missing = sorted(x for x in REQUIRED if row[x] is None)
    if missing: raise RuntimeError(f"{year}년 필수 계정 누락: {', '.join(missing)}")
    return row


def download_documents(key: str, reports: list[dict]) -> None:
    target = ROOT / "reports" / "source"; target.mkdir(parents=True, exist_ok=True)
    for report in reports:
        receipt = report["rcept_no"]
        with urlopen(f"{API}/document.xml?{urlencode({'crtfc_key': key, 'rcept_no': receipt})}", timeout=90) as response:
            (target / f"{receipt}.zip").write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", help="인증키. 없으면 .env의 DART_API_KEY를 사용")
    parser.add_argument("--years", type=int, default=3, help="수집할 최근 연간 사업보고서 수")
    parser.add_argument("--download-documents", action="store_true", help="사업보고서 원문 ZIP도 저장")
    args = parser.parse_args(); load_dotenv(); key = args.api_key or os.environ.get("DART_API_KEY")
    if not key: raise SystemExit("DART_API_KEY가 없습니다. .env.example을 .env로 복사해 설정하세요.")
    years = list(range(date.today().year - args.years - 1, date.today().year + 1))
    rows = []; raw = ROOT / "data" / "raw"; raw.mkdir(parents=True, exist_ok=True)
    for year in years:
        payload = request("fnlttSinglAcntAll.json", {"crtfc_key": key, "corp_code": CORP_CODE, "bsns_year": str(year), "reprt_code": REPORT_CODE, "fs_div": "CFS"})
        if payload.get("status") == "000":
            (raw / f"opendart_sdbiosensor_cfs_{year}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            rows.append(normalise(year, payload["list"]))
    if not rows: raise RuntimeError("수집 가능한 연결 사업보고서 재무제표가 없습니다.")
    rows = sorted(rows, key=lambda x: x["year"])[-args.years:]
    with (ROOT / "data" / "financial_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    disclosures = request("list.json", {"crtfc_key": key, "corp_code": CORP_CODE, "bgn_de": "20190101", "end_de": date.today().strftime("%Y%m%d"), "pblntf_ty": "A", "page_count": "100"})
    annual = [x for x in disclosures.get("list", []) if x.get("report_nm", "").startswith("사업보고서")]
    (ROOT / "reports" / "opendart_disclosures.json").write_text(json.dumps({"rss_url": COMPANY_RSS, "reports": annual}, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.download_documents: download_documents(key, annual)
    print(f"수집 완료: {len(rows)}개 연도, {ROOT / 'data' / 'financial_summary.csv'}")


if __name__ == "__main__": main()
