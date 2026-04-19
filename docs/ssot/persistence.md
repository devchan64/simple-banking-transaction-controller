# Persistence SSOT

## 목적

- banking / controller 검증 지원
- 최소 mock 데이터 제공
- 최소 흐름 지원
- 이후 저장 방식 교체 대비

## 방식

- 카드/계좌 데이터: JSON
- 현재 세션 정보: JSON
- 범위: test only

## 데이터

- `cards.json`
- `accounts.json`
- 현재 구현의 세션 관련 파일
  - `session-history.json`
  - `active-sessions.json`

## 책임

- 카드 데이터 조회
- 계좌 데이터 조회
- 현재 구현에서 필요한 최소 파일 저장 제공

## 구현 기준

- 카드 찾기
- 카드의 계좌 목록 찾기
- 계좌 잔액 읽기
- 입금 후 잔액 저장
- 출금 후 잔액 저장

## 세션 메모

- 장기적으로 세션 생성과 유효기간 관리는 banking 이 책임지는 편이 맞다
- controller 가 세션 생명주기의 단일 저장 원천을 직접 소유하는 구조는 목표가 아니다
- 현재의 `session-history.json` 과 `active-sessions.json` 은 과도기 구조로 본다
- 이후에는 세션 토큰, 만료, refresh, 새 토큰 발급 계약이 banking 쪽으로 더 모이는 편이 자연스럽다

## 구현 키워드

- lightweight storage
- mock repository
- json file store
- transitional session store
- replaceable boundary

## 금지

- 큰 저장소 설계
- prompt 처리
- business rule 재해석
