# Persistence SSOT

## 목적

- controller 검증 지원
- 최소 mock 데이터 제공
- 최소 세션 정보 보관
- 최소 흐름 지원
- 이후 저장 방식 교체 대비

## 방식

- 카드/계좌 데이터: JSON
- 세션 정보: JSON
- 범위: test only

## 데이터

- `cards.json`
- `accounts.json`
- `sessions.json`
- `session_id`
- `authenticated flag`
- `expiration timestamp`

## 책임

- 카드 데이터 조회
- 계좌 데이터 조회
- 세션 조회
- 세션 유효 여부 확인
- 세션 갱신 반영

## 구현 기준

- 카드 찾기
- 카드의 계좌 목록 찾기
- 계좌 잔액 읽기
- 입금 후 잔액 저장
- 출금 후 잔액 저장

## 구현 키워드

- lightweight storage
- mock repository
- json file store
- session file store
- session expiration
- session refresh
- replaceable boundary

## 금지

- 큰 저장소 설계
- prompt 처리
- business rule 재해석
