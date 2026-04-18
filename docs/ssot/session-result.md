# SessionResult API Contract

## 목적

- controller 출력 계약 고정
- controller API 응답 계약 고정
- 표현 계층 출력 기준 고정
- 구현 전 결과 모델 정리

## 모델

- 타입: `SessionResult`
- 반환: `handle(command)` 결과
- 성격: controller API 가 반환하는 유일한 응답 모델

## 필드

- `succeeded`
- `status_code`
- `session_state`
- `session_token`
- `message`
- `available_account_ids`
- `selected_account_id`
- `balance`
- `transaction_type`
- `requested_amount`
- `session_closed`

## 필수 규칙

- `succeeded` 는 항상 포함
- `status_code` 는 항상 포함
- `session_state` 는 항상 포함
- `message` 는 항상 포함
- `session_closed` 는 항상 포함
- 세션이 살아 있으면 `session_token` 포함 가능

## status_code

- 기계 판별용 값
- presenter 가 분기할 때 사용할 수 있는 값
- message 와 분리한다

## message

- 사람에게 보여줄 문장
- 설명 중심 값
- 상태 판별용으로 사용하지 않는다

## 선택 규칙

- 인증 직후 계좌 선택 전이면 `available_account_ids` 포함 가능
- 계좌 선택 이후 `selected_account_id` 포함 가능
- 잔액 조회 결과면 `balance` 포함
- 입금 결과면 `balance` 포함
- 출금 결과면 `balance` 포함
- 거래 결과면 `transaction_type` 포함
- 입금/출금 결과면 `requested_amount` 포함

## transaction_type

- `BALANCE`
- 잔액 조회 결과를 의미한다
- `DEPOSIT`
- 입금 처리 결과를 의미한다
- `WITHDRAW`
- 출금 처리 결과를 의미한다

## 상태 규칙

- 결과의 `session_state` 는 처리 후 상태여야 한다
- 상태 판단은 presenter 가 아니라 controller 가 한다
- 종료 결과면 `session_closed = true`
- 상태코드 판단은 presenter 가 아니라 controller 가 한다

## 출력 규칙

- presenter 는 `SessionResult` 만 보고 출력한다
- presenter 는 상태를 다시 해석하지 않는다
- 추가 비즈니스 규칙은 presenter 에서 수행하지 않는다
- presenter 는 `status_code` 로 분기할 수 있다
- presenter 는 `message` 를 사람에게 그대로 보여줄 수 있다
- presenter 는 `available_account_ids` 를 그대로 보여줄 수 있다

## session 규칙

- 세션 생성 직후 토큰을 결과에 포함할 수 있다
- 세션 만료면 controller 가 실패 또는 종료 결과를 반환한다
- 종료 상태면 이후 입력은 허용하지 않는다

## 구현 키워드

- single output model
- presentation-ready
- explicit state
- deterministic result
