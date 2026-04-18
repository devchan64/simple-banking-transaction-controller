# Persistence SSOT

## 목적

- controller 검증 지원
- 최소 mock 데이터 제공
- 최소 세션 정보 보관

## 방식

- 카드/계좌 데이터: JSON
- 세션 정보: in-memory
- 범위: test only

## 데이터

- `cards.json`
- `accounts.json`
- `session_id`
- `authenticated flag`
- `expiration timestamp`

## 책임

- 카드 데이터 조회
- 계좌 데이터 조회
- 세션 조회
- 세션 유효 여부 확인
- 세션 갱신 반영

## 구현 키워드

- lightweight storage
- mock repository
- json file store
- session expiration
- session refresh

## 금지

- 큰 저장소 설계
- prompt 처리
- business rule 재해석

## 한 줄 정의

Persistence는 controller 검증에 필요한 최소 데이터만 보관하는 작은 mock 저장 계층이다.
