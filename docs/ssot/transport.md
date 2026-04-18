# Transport SSOT

## 목적

- 프로그램 간 호출 연결
- 상태머신 요청 전달
- 최대한 단순하게 구현
- 이후 다른 transport 교체 대비

## 방식

- file-based request
- file-based response
- multi-process friendly

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

- request 파일 작성 또는 전달
- response 파일 읽기 또는 반환
- controller 프로그램과 CLI 프로그램 연결
- 예외를 error response 로 변환

## 구현 키워드

- lightweight
- file transport
- request/response json
- process boundary
- exception mapping
- no business logic
- replaceable boundary

## 금지

- 비즈니스 로직 수행
- 상태 판단
- 입력 해석
