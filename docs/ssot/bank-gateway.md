# BankGateway SSOT

## 목적

- controller 가 banking 기능을 호출하는 포트 정의
- 외부 banking 접근을 controller 에서 분리
- 구현체 교체 가능성 유지

## 성격

- controller 의존 포트
- banking 도메인 접근 계약
- 구현체와 분리된 추상 경계
- mock 친화적 계약

## 경계

- `BankGateway`
  - controller 가 의존하는 포트
  - 카드 조회, PIN 검증, 계좌 조회, 입출금 같은 banking 기능 계약을 표현한다
- transport 기반 구현체
  - 위 포트를 만족시키는 adapter 또는 SDK 역할을 한다
  - request 생성, transport 기록, polling, 응답 역직렬화, 예외 매핑을 담당한다

현재 runtime 기본 구현 이름:

- `BankingSdk`

즉 `BankGateway` 자체는 SDK 가 아니다.
SDK 또는 client 구현체가 `BankGateway` 포트를 구현하는 구조로 이해하는 편이 맞다.

## 제공 기능

- 세션 생성
- 세션 유효기간 확인
- 세션 refresh
- 세션 invalidate
- 필요 시 새 세션 토큰 발급
- 카드 조회
- PIN 검증
- 계좌 목록 조회
- 잔액 조회
- 입금 반영
- 출금 반영

## 책임

- controller 가 필요한 banking 기능 계약 제공
- 세션 생성과 유효기간 정책의 원천 제공
- controller 의 refresh 요청에 대한 세션 재검증 또는 새 토큰 발급 제공
- controller 종료 요청에 대한 세션 invalidate 제공
- 구현체가 교체되어도 controller 흐름 유지
- banking 결과와 오류를 controller 가 다룰 수 있는 형태로 노출

## 비책임

- transport 방식 자체를 표준화하지 않는다
- request/response 파일 형식을 직접 정의하지 않는다
- polling, timeout, 직렬화 세부사항을 포트에 노출하지 않는다
- server process lifecycle 을 포트 책임으로 두지 않는다
- controller 내부 상태머신 저장을 직접 소유하지 않는다

## 구현 기준

- controller 는 `BankGateway` 포트만 안다
- mock 구현과 runtime 구현은 같은 포트를 공유한다
- transport 구현은 포트 뒤에 숨긴다
- 도메인 규칙과 transport 세부사항을 섞지 않는다

## 런타임 구조

- `banking` runtime
  - `mock-db/cards.json`
  - `mock-db/accounts.json`
  - `session-history.json`
  - `active-sessions.json`

## 세션 파일 메모

- `session-history.json`
  - 위치: `banking` runtime root
  - 세션 토큰 발급 이력을 남기는 과도기 파일
- `active-sessions.json`
  - 위치: `banking` runtime root
  - banking 활성 세션을 저장하는 과도기 파일

장기적으로 세션 생성, 만료, refresh, invalidate, 새 토큰 발급은
banking 세션 계약 쪽으로 더 모이는 편이 맞다.

## 구현 키워드

- controller port
- replaceable adapter
- mock-friendly
- domain boundary
- no transport detail leakage
