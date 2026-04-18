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
- `Prompt Adapter`: 테스트용 CLI 도구 / 입력 수집 / `SessionCommand` 변환 / 결과 출력
- `Transport`: 파일 기반 request/response 로 프로그램 간 요청을 잇는 작은 보조 계층
- `BankGateway`: 외부 데이터 접근 / PIN 검증 / 금액 검증을 맡는 작은 연결 도구
- `Persistence`: controller 검증용 최소 mock 저장 / 세션 상태 저장

## 목적

- controller 중심 설계
- 테스트 가능한 구조
- 네트워크 없는 데모 환경
- 최소 구현 흐름 우선
- 확장을 고려한 인터페이스 유지
