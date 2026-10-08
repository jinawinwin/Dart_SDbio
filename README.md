# 에스디바이오센서 DART 재무 분석 에이전트

<a href="https://jinawinwin.github.io/Dart_SDbio/"><img src="assets/dashboard-badge.svg" alt="대시보드 바로가기" width="360"></a>

**대시보드 바로가기:** https://jinawinwin.github.io/Dart_SDbio/

에스디바이오센서(종목코드 137310, DART 고유번호 00854997)의 연결 재무제표를 OpenDART API에서 수집하고, 주요 재무비율을 계산하여 GitHub Pages 대시보드로 시각화합니다.

## 대시보드 구성

- 상단: 핵심 KPI와 매출·영업이익, 수익성, 재무구조, 현금흐름 figures
- 하단: Annual / Half-year / Quarterly 3개 테이블
- Quarterly: DART 누적 손익·현금흐름을 직전 누적값에서 차감하여 분기 단독 실적으로 표시
- 우측 플로팅 창: PDF 저장 및 Excel 다운로드
- Excel 다운로드: Annual / Half-year / Quarterly 중 기간을 선택하여 Excel 호환 xls로 저장
- 하단: 국내 peer firms 비교표

## 데이터 수집·자동 업데이트

scripts/fetch_opendart.py는 2010년부터 현재 연도까지 사업보고서(11011), 반기보고서(11012), 1분기(11013), 3분기(11014) 연결 재무제표를 수집합니다. DART에서 특정 연도의 완전한 연결 재무제표가 반환되지 않는 경우에는 해당 기간을 제외하고 가용기간을 기록합니다.

GitHub Actions는 매월 1일 11:17 KST(02:17 UTC)에 자동 실행됩니다. 저장소의 코드가 변경되어도 업데이트 workflow가 자동 실행되며, 데이터 파일만 변경된 경우에는 재실행 루프가 발생하지 않도록 push path를 제한했습니다. GitHub의 scheduled workflow는 시스템 부하에 따라 지연될 수 있습니다.

### OpenDART API 키

GitHub 저장소의 Settings → Secrets and variables → Actions → New repository secret에서 이름을 DART_API_KEY로 등록합니다.

API key는 코드, README, Issues에 직접 넣지 않습니다. 로컬 실행은 .env.example을 .env로 복사하여 사용할 수 있습니다.

## 실행

    python scripts/fetch_opendart.py --start-year 2010
    python scripts/analyze.py

GitHub Pages가 활성화된 저장소에서는 index.html이 곧 대시보드입니다.

## 국내 Peer Firms

아래 peer group은 국내 상장 체외진단·현장진단 기업 중 사업 유사성을 기준으로 선정한 비교군입니다. 직접적인 1:1 경쟁사라는 의미는 아닙니다.

| 회사 | 종목코드 | 시장 | 주요 영역 | 비교 포인트 |
|---|---:|---|---|---|
| 씨젠 | 096530 | KOSDAQ | 분자진단·PCR | 감염성 질환 중심 체외진단 |
| 바디텍메드 | 206640 | KOSDAQ | POCT·면역진단 | 현장진단 플랫폼/카트리지 |
| 수젠텍 | 253840 | KOSDAQ | 면역진단·신속검사 | 체외진단 시약 및 신속검사 |
| 휴마시스 | 205470 | KOSDAQ | POCT·자가검사 | 현장진단·자가진단 |
| 피씨엘 | 241820 | KOSDAQ | 체외진단·다중검사 | 다중검사 플랫폼 및 시약 |

Peer 선정 참고: 2022년 SD Biosensor 관련 DART 사업보고서는 국내 현장진단(POCT) 경쟁군으로 바디텍메드·엑세스바이오 등을, 코로나19 신속항원검사 경쟁군으로 휴마시스 등을 제시합니다. 이 프로젝트는 여기에 분자진단·체외진단의 국내 상장 비교기업을 보완하여 peer group을 구성합니다.

## 보안·품질 개선

- Actions는 contents: write만 허용
- checkout@v7, setup-python@v7 사용
- workflow concurrency로 중복 실행 방지
- OpenDART 요청에 재시도 3회와 User-Agent 적용
- 금액 0을 결측치로 오인하지 않도록 파싱 수정
- .env 및 로컬 파일을 .gitignore로 차단
- 2Q/3Q/4Q 분기 단독 실적 계산을 자동화
- ROA·ROE·DSO는 평균 잔액 기반으로 계산

## 주요 해석 유의사항

DART 반기·분기 손익 및 현금흐름은 누적 기준일 수 있습니다. 따라서 dashboard의 Quarterly 표에서 2Q·3Q·4Q는 순차 차감하여 분기 단독 값으로 만들었습니다. 대차대조표 항목은 각 기간말 잔액입니다.

본 프로젝트의 peer table은 기업 비교를 위한 연구용 분류이며 투자 권유가 아닙니다.

## Source

- https://opendart.fss.or.kr/
- https://englishdart.fss.or.kr/dsbc001/selectPopup.ax?selectKey=00854997
- https://www.sdbiosensor.com/

## GitHub Pages / 저장소 링크

Dashboard: https://jinawinwin.github.io/Dart_SDbio/
Repository: https://github.com/jinawinwin/Dart_SDbio/

About → Website에는 Dashboard 주소를 등록하면 저장소 오른쪽에서도 바로 접근할 수 있습니다. 현재 GitHub connector에서 Repository의 About/Homepage 메타데이터를 수정하는 쓰기 API는 제공되지 않아, 링크 배지와 README는 자동 반영했습니다.
