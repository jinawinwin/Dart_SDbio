# 유한양행 DART 재무 분석

유한양행(종목코드 `000100`)의 2025년 사업보고서와 연결 기준 재무 수치를 보관하고, 재무비율을 재현 가능하게 계산하는 저장소입니다.

## 기준과 출처

- 보고서: 2025 사업연도(제103기), 제출일 2026-03-12
- DART 접수번호: `20260312004696`
- 원문: `reports/yuhan_2025_business_report_krx.html` — 한국거래소가 제공하는 DART 공시 미러 원문
- 수치 출처: 유한양행 [재무정보](https://www.yuhan.co.kr/Invest/Manage/Finance/)의 요약 연결재무제표. 금액은 모두 원화로 저장합니다.
- 회계 기준: 연결 기준. 손익·현금흐름은 기간 값, 재무상태표는 기말 값입니다.

## OpenDART 수집 및 실행

1. [OpenDART](https://opendart.fss.or.kr/)에서 발급받은 인증키를 `.env`에 넣습니다. `.env`는 Git에 저장되지 않습니다.

```text
DART_API_KEY=발급받은_40자리_인증키
```

2. 연결 재무제표(CFS)를 수집하고 대시보드 데이터를 갱신합니다.

```powershell
python scripts/fetch_opendart.py
python scripts/analyze.py
```

`fetch_opendart.py`는 OpenDART 단일회사 재무제표 API로 2023~2025 사업보고서(`11011`)를 수집합니다. 응답 원문은 `data/raw/`에, 정규화된 값은 `data/financial_summary.csv`에 보관됩니다. `--download-documents`를 추가하면 각 사업보고서 원문 ZIP도 `reports/source/`에 내려받습니다(대용량 파일은 기본적으로 Git에서 제외).

## 대시보드

저장소 루트의 `index.html`은 GitHub Pages용 정적 대시보드입니다. `data/dashboard.json`을 읽기 때문에 API 키가 브라우저나 GitHub에 노출되지 않습니다. GitHub 저장소 설정에서 **Settings → Pages → Deploy from a branch → main / (root)**를 선택하면 공개할 수 있습니다.

## 분석 실행

```powershell
python scripts/analyze.py
```

실행하면 `data/ratios.csv`, `data/dashboard.json` 및 `analysis/2025_financial_analysis.md`를 다시 만듭니다. 외부 패키지가 필요 없습니다.

## 지표 정의

- 영업이익률 = 영업이익 / 매출액
- 순이익률 = 당기순이익 / 매출액
- 유동비율 = 유동자산 / 유동부채
- 부채비율 = 부채총계 / 자본총계
- 자기자본비율 = 자본총계 / 자산총계
- ROA = 당기순이익 / 평균자산, ROE = 당기순이익 / 평균자본
- CFO 전환율 = 영업활동현금흐름 / 당기순이익
- 매출채권회전일수(DSO) = 평균 매출채권 / 매출액 x 365

가이드의 원칙에 따라 ROA·ROE·DSO는 평균 잔액을 사용합니다. CAPEX가 명확하게 분리된 원자료를 별도로 검증하기 전에는 FCF와 ROIC를 산출하지 않습니다.

## 유의사항

2025년 순이익에는 관계기업 투자주식 및 투자부동산 처분 관련 이익 등 비경상 항목이 포함될 수 있습니다. 따라서 순이익률, ROA, ROE는 영업이익률·CFO 전환율과 함께 해석해야 합니다. 이 저장소는 투자 권유가 아닙니다.
