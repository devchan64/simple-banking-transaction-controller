# BankGateway SSOT

## 목적

- controller 검증 지원
- 외부 데이터 접근 연결
- 최소 흐름 지원

## 성격

- 작은 연결 도구
- controller 의존 포트
- mock 중심 도구
- 교체 가능한 경계

## 방식

- 카드 조회
- 계좌 조회
- 잔액 조회
- 입금 반영
- 출금 반영

## 책임

- controller 요청 전달
- persistence 접근 위임
- PIN 검증
- 금액 검증
- 필요한 데이터 반환

## 구현 기준

- 카드 확인
- PIN 확인
- 계좌 목록 확인
- 잔액 반환
- 입금 반영
- 출금 반영

## 구현 키워드

- thin gateway
- simple bridge
- mock-friendly
- bank data validation
- amount validation
