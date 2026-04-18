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
- 확장성: socket, HTTP, 실DB adapter 대응

## 계층

- `Controller`: `handle(command)` / 상태 검증 / 상태 전이 / 결과 생성 / 세션 인증 확인 / 세션 만료 확인 / 세션 갱신 처리
- `Prompt Adapter`: 입력 수집 / `SessionCommand` 변환 / 결과 출력
- `Transport`: controller 호출만 넘기는 작은 보조 계층
- `BankGateway`: controller 의존 포트 / 외부 데이터 접근 연결
- `Persistence`: controller 검증용 최소 mock 저장

## 목적

- controller 중심 설계
- 테스트 가능한 구조
- 네트워크 없는 데모 환경
- 실제 인프라로 확장 가능한 경계 유지
