# BankGateway SSOT

## 목적

- controller 검증 지원
- 외부 데이터 접근 연결
- 최대한 단순하게 구현

## 성격

- 작은 연결 도구
- controller 의존 포트
- mock 중심 도구

## 방식

- 카드 조회
- 계좌 조회
- 잔액 조회
- 입금 반영
- 출금 반영

## 책임

- controller 요청 전달
- persistence 접근 위임
- 필요한 데이터 반환

## 구현 키워드

- thin gateway
- simple bridge
- mock-friendly
- no business logic

## 한 줄 정의

BankGateway는 controller와 mock 저장 계층 사이를 잇는 작은 연결 도구이다.
