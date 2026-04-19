# Banking Session Controller

가상 ATM CLI 세션 흐름 SSOT 정리 프로젝트

## 핵심

- 중심: `Controller`
- 역할: 세션 상태머신 제어
- 목표: 비즈니스 규칙 집중
- 원칙: 나머지 계층은 단순화

## 방향

- 상태: 카드 입력부터 세션 종료까지 일관된 흐름
- 구조: 책임 분리
- 우선순위: controller 검증 가능성
- 구현 전략: mock 우선, 단순성 우선
- 기준: 카드 삽입 / PIN / 계좌 선택 / 잔액 조회 / 입금 / 출금
- 설계: 이후 교체 가능한 경계 유지

## 계층

- `Controller`: `handle(command)` / 세션 검증 / 상태 전이 / 결과 생성 / 세션 만료 확인 / 세션 갱신 처리
- `SessionCommand`, `SessionResult`: controller API 계약
- `Prompt Adapter`: 테스트용 CLI 도구 / 입력 수집 / `SessionCommand` 변환 / 결과 출력
- `Transport`: 파일 기반 request/response 로 프로그램 간 요청을 잇는 작은 보조 계층
- `BankGateway`: 외부 데이터 접근 / PIN 검증 / 금액 검증을 맡는 작은 연결 도구
- `Persistence`: controller 검증용 최소 mock 저장 / 세션 상태 저장

경계 메모:
- `Transport` 는 통신 수단이다
- `BankGateway` 는 controller 가 의존하는 banking 기능 포트다
- file transport 기반 banking 구현은 transport 를 사용하는 adapter 또는 SDK/client 이지만,
  controller 에서는 `BankGateway` 구현체로 주입된다

세션 메모:
- 장기적으로 세션 생성과 유효기간 관리는 `banking` 이 책임지는 구조를 목표로 한다
- `controller` 는 banking 이 발급한 세션 토큰과 유효기간 정보를 신뢰해 흐름을 제어한다
- 현재의 `session-history.json` 과 `active-sessions.json` 구조는 과도기 구현이다

## 목적

- controller 중심 설계
- 테스트 가능한 구조
- 네트워크 없는 데모 환경
- 최소 구현 흐름 우선
- 확장을 고려한 인터페이스 유지

## 개발 환경

- `requirements.txt` 기준 의존성 설치
- 핵심 의존성: `pydantic`
- Python `3.12.3` 사용
- Python 3
- Bash
- 로컬 파일시스템 기반 실행 환경
- 네트워크 없이 동작하는 mock banking / controller / transport 구조

일상적인 개발 순서:
- `bash scripts/setup.sh`
- `bash scripts/test-basic.sh`
- 필요 시 `bash scripts/test-e2e.sh`

## 실행

- 환경 준비: `bash scripts/setup.sh`
- 코드 포맷: `bash scripts/run-black.sh`
- 바이트 검사: `bash scripts/check-bytes.sh`
- transport 정리: `bash scripts/clean-transport.sh`
- controller 정리: `bash scripts/clean-controller.sh`
- banking 정리: `bash scripts/clean-banking.sh`
- 전체 정리: `bash scripts/clean-all.sh`

## 테스트

- 기본 테스트 실행: `bash scripts/test-basic.sh`
- E2E 테스트 실행: `bash scripts/test-e2e.sh`
- 전체 테스트 실행: `bash scripts/test-all.sh`

기본 테스트 범위:
- `tests/banking`
- `tests/controller`
- `tests/transport`

E2E 테스트 범위:
- `tests/e2e`

## 서버 구동

- banking 서버 실행: `bash scripts/run-banking-server.sh`
- controller 서버 실행: `bash scripts/run-controller-server.sh`
- ATM CLI Prompt Adapter 실행: `bash scripts/run-atm-cli.sh`

포어그라운드 실행 예:
```bash
bash scripts/run-banking-server.sh
```

다른 터미널에서 controller 서버 실행:
```bash
bash scripts/run-controller-server.sh
```

또 다른 터미널에서 사람이 직접 controller 절차를 테스트하려면:
```bash
bash scripts/run-atm-cli.sh
```

`Prompt Adapter`는 유저 테스트용 CLI 도구입니다.
- 카드 번호 입력
- PIN 입력
- 계좌 선택
- 잔액 조회 / 입금 / 출금 / 카드 반환

을 사람 입력으로 진행하면서 controller 응답 메시지를 그대로 보여줍니다.

## Prompt Adapter 실행 방법

1. banking 서버 실행
```bash
bash scripts/run-banking-server.sh
```

2. 다른 터미널에서 controller 서버 실행
```bash
bash scripts/run-controller-server.sh
```

3. 또 다른 터미널에서 Prompt Adapter 실행
```bash
bash scripts/run-atm-cli.sh
```

기본 경로는 다음과 같습니다.
- transport: `.transport`
- banking server runtime: `.banking`
- controller server runtime: `.controller`
- Prompt Adapter: `.transport`로 request/response 파일을 보냄

다른 controller runtime 경로를 사용할 때:
```bash
bash scripts/run-atm-cli.sh /path/to/transport-root
```

controller 서버의 transport/runtime/banking 경로를 각각 바꾸려면:
```bash
bash scripts/run-controller-server.sh /path/to/transport-root /path/to/controller-runtime /path/to/banking-root
```

## 디렉터리 용도

참고용 실행 디렉터리는 다음과 같습니다.

- `.transport`
  - Prompt Adapter와 controller 서버가 request/response 파일을 주고받는 전송 경계
- `.controller`
  - controller 서버의 현재 상태 저장 경계
  - `session-history.json`, `active-sessions.json`이 생성됨
- `.banking`
  - banking 서버의 실행 경계
  - bank용 `mock-db`, `session-history.json`, `active-sessions.json`이 생성됨
- `.test-run`
  - 테스트 실행 중 임시 산출물을 모으는 디렉터리
  - 기본 테스트와 E2E 테스트가 매 실행마다 다시 만듦
