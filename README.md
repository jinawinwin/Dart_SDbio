# 에스디바이오센서 DART 재무 분석 에이전트

[![대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97-%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-0969da?style=for-the-badge)](https://jinawinwin.github.io/SDbio_dart/)

에스디바이오센서(종목코드 `137310`, DART 고유번호 `00854997`)의 연결 재무제표를 OpenDART API에서 수집하고, 주요 재무비율을 계산해 GitHub Pages 대시보드로 표시합니다. 2010년부터 현재까지 연간·1분기·반기·3분기 공시를 수집하며, 이후 공시는 GitHub Actions가 매주 자동 점검합니다.

## 포함 내용

- `scripts/fetch_opendart.py`: 2010년부터 연간(`11011`)·1분기(`11013`)·반기(`11012`)·3분기(`11014`) 연결 재무제표를 수집하고 원문 응답을 `data/raw/`에 저장합니다. 제공한 [기업 RSS](https://dart.fss.or.kr/api/companyRSS.xml?crpCd=00854997) 주소도 기록합니다.
- `scripts/analyze.py`: 동일 보고서 유형의 전년 기간과 비교해 수익성, 유동성, 안정성, 현금흐름, 활동성 지표를 계산합니다. ROA·ROE·DSO에는 평균 잔액을 적용합니다.
- `index.html`: API 키를 노출하지 않고 계산된 JSON만 읽는 GitHub Pages 정적 대시보드입니다.
- `.github/workflows/update-data.yml`: 매월과 수동 실행 시 데이터를 갱신하고 변경된 수치만 자동 커밋합니다.

## OpenDART API 키 설정

1. [OpenDART](https://opendart.fss.or.kr/)에서 인증키를 발급받습니다.
2. 로컬에서는 `.env.example`을 `.env`로 복사한 뒤 다음처럼 입력합니다. `.env`는 Git에 올라가지 않습니다.

```text
DART_API_KEY=발급받은_인증키
```

3. GitHub 저장소 `jinawinwin/SDbio_dart`의 **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 `DART_API_KEY`로 지정하고 같은 키를 등록합니다. 키를 코드·README·Issues에 올리지 마세요.

## 처음 실행

```powershell
python scripts/fetch_opendart.py --start-year 2010
python scripts/analyze.py
```

생성되는 `data/financial_summary.csv`, `data/ratios.csv`, `data/dashboard.json`을 확인한 뒤 커밋·푸시합니다. 분기·반기 손익과 현금흐름은 DART의 누적값일 수 있으므로, 분기 단독 실적 해석에는 전 분기 값 차감이 필요합니다.

## GitHub 업로드와 대시보드 공개

ZIP을 푼 폴더에서 다음을 실행합니다.

```powershell
git init
git branch -M main
git remote add origin https://github.com/jinawinwin/SDbio_dart.git
git add .
git commit -m "feat: add SD Biosensor OpenDART dashboard"
git push -u origin main
```

이후 GitHub의 **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)`**로 설정합니다. Actions 탭에서 **Update OpenDART financial data → Run workflow**를 실행하면 최초 자동 수집을 수행합니다.

## 지표와 한계

영업이익률, 순이익률, 유동비율, 부채비율, 자기자본비율, ROA, ROE, CFO 전환율, DSO, CAPEX가 식별될 때 FCF를 제공합니다. EBITDA·ROIC·순차입금·PER·PBR·EV/EBITDA는 신뢰할 수 있는 감가상각·세율·차입금·시가 데이터가 이 프로젝트의 OpenDART 요약 수치만으로 확정되지 않아 계산하지 않습니다. 비경상 손익과 계정명 차이는 사업보고서 주석으로 추가 검토해야 하며, 본 프로젝트는 투자 권유가 아닙니다.
