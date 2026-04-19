# Transport SSOT

## 목적

- 프로그램 간 호출 연결
- 상태머신 요청 전달
- 최대한 단순하게 구현
- 이후 다른 transport 교체 대비

## 경계

- `Transport`
  - 프로세스 사이에서 request/response 를 옮기는 전송 경계
- `BankGateway`
  - controller 가 의존하는 banking 기능 포트
- transport 기반 banking adapter
  - transport 를 사용해 banking 서버를 호출하지만,
    controller 쪽에서는 `BankGateway` 구현체로 보인다

즉 transport 는 통신 수단이고,
`BankGateway` 는 controller 포트이며,
transport 기반 banking adapter 는 그 둘을 연결하는 구현체다.

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

## 비책임

- banking 도메인 규칙 계산
- PIN 검증, 잔액 계산, 입출금 정책 결정
- controller 상태 전이 판단
- banking SDK/client 포트 정의

## 구분 메모

- transport 자체는 business API 가 아니다
- transport 자체는 banking port 가 아니다
- file transport 를 이용하는 banking SDK/client 는 transport 위에 올라가는 별도 adapter 이다
- 따라서 transport 문서와 bank gateway 문서는 함께 읽되, 같은 경계로 취급하지 않는다

## 구현 키워드

- lightweight
- file transport
- request/response json
- process boundary
- exception mapping
- no business logic
- replaceable boundary
