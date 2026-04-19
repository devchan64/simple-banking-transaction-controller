# Persistence JSON SSOT

---

## 목적

- 최소 JSON 목록 정리
- 최소 구현 흐름 기준 정리

---

## cards.json

- `card_id`
- `card_number`
- `cardholder_name`
- `expires_at`
- `status`
- `pin`
- `account_ids`

---

## accounts.json

- `account_id`
- `balance`

---

## 현재 세션 관련 파일

- `session-history.json`
  - 현재 구현에서 발급 이력을 남기는 과도기 파일
- `active-sessions.json`
  - 현재 구현에서 controller 상태를 저장하는 과도기 파일

장기적으로 세션 생성, 만료, refresh, 새 토큰 발급은
banking 세션 계약 쪽으로 더 모이는 편이 맞다.

---

## 현재 우선순위

- 필수: `cards.json`
- 필수: `accounts.json`
- 세션 파일은 현재 과도기 구현 기준

---

## 구현 기준

- 카드 삽입
- PIN 번호 입력
- 계좌 선택
- 잔액 조회
- 입금
- 출금

---
