# Transport SSOT

## 목적

- controller 호출 감싸기
- 테스트 흐름 유지
- 최대한 단순하게 구현

## 방식

- in-process call
- function dispatch

## 포트

- `dispatch(request) -> response`

## 입력

- `request_id`
- `session_id`
- `command`

## 출력

- `request_id`
- `result`
- `error_code`
- `error_message`

## 책임

- controller 호출
- 예외를 error response 로 변환

## 구현 키워드

- lightweight
- pass-through
- exception mapping
- no business logic

## 금지

- 비즈니스 로직 수행
- 상태 판단
- 입력 해석

## 한 줄 정의

Transport는 controller 호출만 넘겨주는 작은 pass-through 계층이다.
