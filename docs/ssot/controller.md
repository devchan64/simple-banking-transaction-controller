# Controller SSOT

## 목적

- 중심 계층
- 세션 상태머신 제어
- 비즈니스 규칙 집중

## 책임

- `handle(command)` 단일 진입점
- `SessionCommand` 계약 검증
- 세션 상태 검증
- 상태 전이 수행
- `BankGatewayPort` 호출 orchestration
- `SessionResult` 생성

## 입력

- 타입: `SessionCommand`
- 방식: command 기반 진입
- 규칙: 잘못된 입력은 throw

## 출력

- 타입: `SessionResult`
- 목적: 표현 계층이 바로 렌더링 가능한 결과

## 상태

- 범위: `IDLE -> CARD_INSERTED -> AUTHENTICATED -> ACCOUNT_SELECTED -> TRANSACTION_EXECUTED -> RESULT_REPORTED -> SESSION_CLOSED`
- 규칙: 역방향 금지
- 규칙: 상태 스킵 금지
- 규칙: 종료 후 입력 금지

## 의존성

- 직접 의존: `BankGatewayPort`
- 비의존: CLI
- 비의존: transport
- 비의존: JSON
- 비의존: filesystem

## 구현 키워드

- pure domain logic
- fail-fast
- explicit state transition
- deterministic result

## 금지

- prompt 출력
- printf 출력
- 사용자 입력 파싱
- transport 처리
- repository 직접 접근

## 한 줄 정의

Controller는 세션 규칙과 상태 전이를 전담하는 핵심 계층이다.
