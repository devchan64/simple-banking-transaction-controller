# Prompt Adapter SSOT

## 목적

- CLI 도구
- controller 검증 지원
- 최소 흐름 실행

## 성격

- 테스트용 보조 도구
- 가벼운 실행 도구
- 문자열 기반 도구

## 방식

- prompt 출력
- 사용자 입력 수집
- 문자열 -> `SessionCommand`
- 결과 출력

## 책임

- CLI 입력 받기
- command 변환
- transport 호출
- 결과 표시

## 구현 기준

- 카드 입력
- PIN 입력
- 계좌 선택
- 잔액 조회 선택
- 입금 선택
- 출금 선택

## 구현 키워드

- cli tool
- test helper
- lightweight
- interactive input
- command conversion

