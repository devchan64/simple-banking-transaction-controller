# SessionCommand API Contract

## 목적

- controller 입력 계약 고정
- controller API 요청 계약 고정
- command 기반 진입 고정
- 구현 전 입력 모델 정리

## 모델

- 타입: `SessionCommand`
- 진입: `handle(command)`
- 성격: controller API 로 들어가는 유일한 요청 모델

## 필드

- `command_type`
- `session_token`
- `card_number`
- `pin`
- `account_id`
- `amount`

## command_type

- `INSERT_CARD`
- 카드 번호를 전달해서 세션 시작을 요청한다
- `SUBMIT_PIN`
- 현재 세션의 카드에 대해 PIN 인증을 요청한다
- `SELECT_ACCOUNT`
- 인증 이후 사용할 계좌 선택을 요청한다
- `REQUEST_BALANCE`
- 선택된 계좌의 현재 잔액 조회를 요청한다
- `REQUEST_DEPOSIT`
- 선택된 계좌에 금액 입금을 요청한다
- `REQUEST_WITHDRAW`
- 선택된 계좌에서 금액 출금을 요청한다
- `END_SESSION`
- 현재 세션 종료를 요청한다

## 필수 규칙

- `command_type` 는 항상 필수
- `session_token` 은 첫 진입 이후 필수
- `INSERT_CARD` 는 `card_number` 필요
- `SUBMIT_PIN` 는 `pin` 필요
- `SELECT_ACCOUNT` 는 `account_id` 필요
- `REQUEST_DEPOSIT` 는 `amount` 필요
- `REQUEST_WITHDRAW` 는 `amount` 필요

## 금지 규칙

- `INSERT_CARD` 에 `pin` 금지
- `INSERT_CARD` 에 `account_id` 금지
- `INSERT_CARD` 에 `amount` 금지
- `SUBMIT_PIN` 에 `account_id` 금지
- `SUBMIT_PIN` 에 `amount` 금지
- `SELECT_ACCOUNT` 에 `pin` 금지
- `SELECT_ACCOUNT` 에 `amount` 금지
- `REQUEST_BALANCE` 에 `card_number` 금지
- `REQUEST_BALANCE` 에 `pin` 금지
- `REQUEST_BALANCE` 에 `account_id` 금지
- `REQUEST_BALANCE` 에 `amount` 금지
- `END_SESSION` 에 `card_number` 금지
- `END_SESSION` 에 `pin` 금지
- `END_SESSION` 에 `account_id` 금지
- `END_SESSION` 에 `amount` 금지

## amount 규칙

- 정수
- `amount > 0`
- 금액 검증은 `BankGateway`

## session 규칙

- 세션 생성은 `INSERT_CARD` 이후 시작
- 세션 검증은 `Controller`
- 세션 만료 확인은 `Controller`
- 세션 갱신 판단은 `Controller`

## 구현 키워드

- single input model
- command-driven
- fail-fast
- explicit contract
