"""OpenDART에서 유한양행 연결 연간 재무제표를 수집한다.

API 키는 --api-key 또는 프로젝트 루트의 .env DART_API_KEY에서 읽는다.
외부 라이브러리 없이 동작한다.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://opendart.fss.or.kr/api"
CORP_CODE = "00145109"  # 유한양행
REPORT_CODE = "11011"  # 사업보고서
YEARS = (2023, 2024, 2025)

ACCOUNT_NAMES = {
    "revenue": {"매출액", "수익(매출액)", "영업수익"},
    "operating_income": {"영업이익", "영업이익(손실)"},
    "profit_before_tax": {"법인세비용차감전순이익", "법인세비용차감전순이익(손실)"},
    "net_income": {"당기순이익", "당기순이익(손실)"},
    "current_assets": {"유동자산"},
    "noncurrent_assets": {"비유동자산"},
    "total_assets": {"자산총계"},
    "current_liabilities": {"유동부채"},
    "noncurrent_liabilities": {"비유동부채"},
    "total_liabilities": {"부채총계"},
    "total_equity": {"자본총계"},
    "operating_cash_flow": {"영업활동으로 인한 현금흐름", "영업활동현금흐름"},
    "investing_cash_flow": {"투자활동으로 인한 현금흐름", "투자활동현금흐름"},
    "financing_cash_flow": {"재무활동으로 인한 현금흐름", "재무활동현금흐름"},
    "cash_and_cash_equivalents": {"현금및현금성자산", "현금 및 현금성자산"},
    "accounts_receivable": {"매출채권", "매출채권 및 기타채권"},
    "inventory": {"재고자산"},
}
FIELDS = ["year", *ACCOUNT_NAMES]


def load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def get_json(endpoint: str, params: dict[str, str]) -> dict:
    url = f"{API}/{endpoint}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def amount(value: str | None) -> int | None:
    if not value or value in {"-", "0"}:
        return None
    return int(value.replace(",", ""))


def normalize(year: int, records: list[dict]) -> dict[str, int | None]:
    row: dict[str, int | None] = {field: None for field in FIELDS}
    row["year"] = year
    for field, names in ACCOUNT_NAMES.items():
        matches = [item for item in records if item.get("account_nm", "").strip() in names]
        # 동일 계정이 여러 재무제표에 있을 수 있으므로 연결(CFS)의 대표 값을 우선한다.
        preferred = next((item for item in matches if item.get("fs_div") == "CFS"), None)
        if preferred:
            row[field] = amount(preferred.get("thstrm_amount"))
    missing = [field for field in ACCOUNT_NAMES if row[field] is None]
    if missing:
        raise RuntimeError(f"{year}년 필수 계정을 찾지 못했습니다: {', '.join(missing)}")
    return row


def save_documents(key: str, disclosures: list[dict]) -> None:
    target = ROOT / "reports" / "source"
    target.mkdir(parents=True, exist_ok=True)
    for item in disclosures:
        receipt = item["rcept_no"]
        path = target / f"{receipt}.zip"
        with urlopen(f"{API}/document.xml?{urlencode({'crtfc_key': key, 'rcept_no': receipt})}", timeout=60) as response:
            path.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", help="OpenDART 인증키. 없으면 .env의 DART_API_KEY 사용")
    parser.add_argument("--download-documents", action="store_true", help="사업보고서 원문 ZIP도 다운로드")
    args = parser.parse_args()
    load_dotenv()
    key = args.api_key or os.environ.get("DART_API_KEY")
    if not key:
        raise SystemExit("DART_API_KEY가 없습니다. .env.example을 .env로 복사해 인증키를 설정하세요.")

    raw_dir = ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for year in YEARS:
        response = get_json("fnlttSinglAcntAll.json", {
            "crtfc_key": key, "corp_code": CORP_CODE, "bsns_year": str(year),
            "reprt_code": REPORT_CODE, "fs_div": "CFS",
        })
        if response.get("status") != "000":
            raise RuntimeError(f"{year}년 OpenDART 오류 {response.get('status')}: {response.get('message')}")
        (raw_dir / f"opendart_yuhan_cfs_{year}.json").write_text(
            json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        rows.append(normalize(year, response["list"]))

    with (ROOT / "data" / "financial_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    disclosures = get_json("list.json", {
        "crtfc_key": key, "corp_code": CORP_CODE, "bgn_de": "20230101", "end_de": "20261231",
        "pblntf_ty": "A", "page_count": "100",
    })
    annual = [item for item in disclosures.get("list", []) if item.get("report_nm", "").startswith("사업보고서")]
    (ROOT / "reports" / "opendart_disclosures.json").write_text(
        json.dumps(annual, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.download_documents:
        save_documents(key, annual)
    print("OpenDART 수집 완료: data/financial_summary.csv")


if __name__ == "__main__":
    main()
