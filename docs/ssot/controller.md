# Controller SSOT

## 목적

- 중심 계층
- 세션 상태머신 제어
- 비즈니스 규칙 집중

## 책임

- `handle(command)` 단일 진입점
- `SessionCommand` 계약 검증
- banking 이 발급한 세션 토큰 사용
- 세션 정보 조회
- 세션 상태 검증
- 상태 전이 수행
- 세션 만료 확인
- 세션 갱신 요청
- `BankGatewayPort` 호출 orchestration
- 인증 직후 계좌 목록 조회 결과 생성
- `SessionResult` 생성

## 입력

- 타입: `SessionCommand`
- 방식: command 기반 API 요청
- 규칙: 잘못된 입력은 throw

## 출력

- 타입: `SessionResult`
- 목적: 표현 계층이 바로 렌더링 가능한 API 응답

## 상태

- 범위: `IDLE -> CARD_INSERTED -> AUTHENTICATED -> ACCOUNT_SELECTED -> TRANSACTION_EXECUTED -> RESULT_REPORTED -> SESSION_CLOSED`
- 규칙: 역방향 금지
- 규칙: 상태 스킵 금지
- 규칙: 종료 후 입력 금지

## 세션 처리

- 세션 생성 주체는 banking 이다
- controller 는 banking 이 발급한 세션 토큰을 받아 이후 처리에 사용한다
- controller 는 세션 토큰으로 banking 과 통신할 수 있어야 한다
- controller 는 세션 유효기간을 신뢰해 클라이언트 후속 처리를 진행할 수 있어야 한다
- controller 는 세션 만료를 감지할 수 있어야 한다
- controller 는 필요 시 banking 에 세션 refresh 와 새 토큰을 요청할 수 있어야 한다
- controller 는 만료된 세션으로 후속 처리를 진행하면 안 된다
- controller 가 세션 생명주기의 단일 저장 원천을 직접 소유하면 안 된다
- controller 의 로컬 파일 기록은 세션 lifecycle manager 가 아니라 절차 기록 용도다

## 의존성

- 직접 의존: `BankGatewayPort`
- 직접 의존: 세션 토큰을 포함한 banking 세션 계약
- 비의존: CLI
- 비의존: transport
- 비의존: JSON
- 비의존: filesystem

## 구현 키워드

- pure domain logic
- fail-fast
- explicit state transition
- deterministic result
- session validation
- session refresh
- session expiration check
~~~~
