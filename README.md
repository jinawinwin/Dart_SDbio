# 에스디바이오센서 DART 재무 분석 에이전트

<a href="https://jinawinwin.github.io/Dart_SDbio/"><img src="assets/sdbiosensor-logo.jpg" alt="대시보드 바로가기" width="360"></a>

**🔗 대시보드 바로가기:** https://jinawinwin.github.io/Dart_SDbio/

에스디바이오센서(종목코드 137310, DART 고유번호 00854997)의 연결 재무제표를 OpenDART API에서 수집하고, 주요 재무비율을 계산하여 GitHub Pages 대시보드로 시각화합니다.

## 대시보드

상단에는 핵심 KPI와 함께 매출·영업이익, 수익성, 재무구조, 현금흐름 figures를 배치하고, 하단에는 **Annual / Half-year / Quarterly** 3개 데이터 테이블을 제공합니다.

Quarterly 표에서는 DART의 누적 손익·현금흐름을 직전 누적값에서 차감하여 분기 단독 실적으로 표시합니다. 대차대조표 항목은 각 기간말 잔액입니다.

대시보드 오른쪽의 고정 다운로드 창에서:
- 🖨 **PDF 저장:** 현재 대시보드 전체를 브라우저 인쇄/PDF로 저장
- 📊 **Excel 다운로드:** Annual / Half-year / Quarterly 중 기간을 선택하여 해당 기간의 **.xlsx** 파일 다운로드

## 데이터 수집·자동 업데이트

<code>scripts/fetch_opendart.py</code>는 **2010년부터 현재 연도까지** 다음 보고서를 순차 수집합니다.

- 사업보고서: 11011
- 반기보고서: 11012
- 1분기보고서: 11013
- 3분기보고서: 11014

OpenDART에서 완전한 연결 재무제표가 반환되지 않는 기간은 오류로 전체 작업을 중단하지 않고 해당 기간만 제외하며, <code>data/dashboard.json</code>에 가용연도와 제외연도를 기록합니다.

GitHub Actions는 **매월 1일 02:17 UTC(11:17 KST)**에 실행되며, 수동 <code>workflow_dispatch</code>도 지원합니다. 데이터가 갱신되면 분석 → Excel 파일 생성 → 구조 검증 → <code>data</code>, <code>reports</code>, <code>downloads</code> 자동 커밋 순으로 진행됩니다.

코드/README/대시보드/워크플로 변경 시에도 자동 실행되도록 구성했으며, 데이터 커밋 자체는 path filter 때문에 같은 workflow가 다시 실행되지 않습니다.

### OpenDART API 키

GitHub 저장소의 **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 **<code>DART_API_KEY</code>**로 등록합니다.

실제 API 키는 코드, README, Issues, 데이터 파일에 직접 저장하지 않습니다. 로컬 실행은 <code>.env.example</code>을 <code>.env</code>로 복사하여 사용할 수 있습니다.

## 실행

<pre>python scripts/fetch_opendart.py --start-year 2010
python scripts/analyze.py
python scripts/build_downloads.py
python scripts/validate_dashboard.py</pre>

필요 패키지는 <code>requirements.txt</code>의 <code>openpyxl</code>뿐입니다.

## 국내 Peer Firms

국내 상장 체외진단·현장진단 기업 중 사업 유사성을 기준으로 선정한 비교군입니다. 직접적인 1:1 경쟁사라는 의미는 아닙니다.

| 회사 | 종목코드 | 시장 | 주요 영역 | 비교 포인트 |
|---|---:|---|---|---|
| 씨젠 | 096530 | KOSDAQ | 분자진단·PCR | 감염성 질환 중심 체외진단 |
| 바디텍메드 | 206640 | KOSDAQ | 현장진단(POCT)·면역진단 | 현장진단 플랫폼·카트리지 |
| 수젠텍 | 253840 | KOSDAQ | 면역진단·신속검사 | 체외진단 시약 및 신속검사 |
| 휴마시스 | 205470 | KOSDAQ | 현장진단·자가검사 | POCT 및 자가진단 제품군 |
| 피씨엘 | 241820 | KOSDAQ | 체외진단·다중검사 | 검사 플랫폼 및 시약 |

SD Biosensor의 국내 경쟁·비교군을 구성할 때 현장진단(POCT), 면역진단, 분자진단, 신속검사 영역의 사업 유사성을 함께 고려했습니다. DART의 2026년 정기공시가 제공되고 있어 향후 peer rationale을 추가 보완할 수 있습니다.

## 보안·품질 관리

- GitHub Actions 권한을 <code>contents: write</code>로 최소화
- <code>actions/checkout@v7</code>, <code>actions/setup-python@v7</code> 사용
- workflow concurrency로 중복 실행 방지
- OpenDART HTTP 요청 재시도 3회 및 User-Agent 적용
- 금액 0을 결측치로 오인하지 않도록 파싱
- 2Q·3Q·4Q 분기 단독 실적 자동 산출
- ROA·ROE·DSO는 평균 잔액 기반 계산
- 대시보드/다운로드 파일에 대한 자동 구조 검증 단계 추가

## 데이터 해석 유의사항

OpenDART의 반기·분기 손익 및 현금흐름은 누적 기준으로 제공되는 항목이 있습니다. 따라서 dashboard의 Quarterly에서 Q2/Q3/Q4는 직전 누적값을 차감하여 분기 단독 실적으로 계산합니다.

2010년부터 수집을 시도하지만, 기업 공시·연결 재무제표의 가용성에 따라 실제 대시보드의 최초 유효 연도는 2010년보다 늦을 수 있습니다.

본 프로젝트의 peer table은 연구용 비교 분류이며 투자 권유가 아닙니다.

## Source

- https://opendart.fss.or.kr/
- https://englishdart.fss.or.kr/dsbc001/selectPopup.ax?selectKey=00854997
- https://www.sdbiosensor.com/

## GitHub Pages / 저장소 링크

**Dashboard:** https://jinawinwin.github.io/Dart_SDbio/  
**Repository:** https://github.com/jinawinwin/Dart_SDbio/

### About → Website

GitHub 저장소 오른쪽 **About** 영역의 **Website**에는 아래 Dashboard URL을 넣으면 저장소 화면에서도 바로 이동할 수 있습니다.

<code>https://jinawinwin.github.io/Dart_SDbio/</code>

현재 연결된 GitHub 도구에는 Repository의 About/Homepage 메타데이터를 수정하는 쓰기 API가 제공되지 않아, **README의 클릭형 링크 배지와 Dashboard 자체는 자동 반영했으며 About → Website만 GitHub 저장소 화면에서 한 번 입력해야 합니다.**
