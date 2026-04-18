# test_controller_spec

## 목적

- `BankingFlowController`의 상태머신 흐름을 스펙으로 고정한다.
- 정상 흐름과 실패 흐름을 함께 검증한다.

## 검증 범위

- `INSERT_CARD` 로 세션 시작
- `SUBMIT_PIN` 성공 후 계좌 목록 반환
- `SUBMIT_PIN` 실패 후 `CARD_INSERTED` 상태 유지
- 인증 전 계좌 선택 거부
- 계좌 선택 전 잔액 조회 거부
- 잘못된 `account_id` 선택 거부
- 잘못된 `account_id` 선택 후 `AUTHENTICATED` 상태 유지
- 잘못된 PIN 입력 거부
- 잔액 조회 결과 보고
- 입금 후 결과 보고
- 출금 후 `FORCE_END_SESSION` 으로 세션 종료
- 잔액 부족 출금 거부
- 잔액 부족 출금 후 `ACCOUNT_SELECTED` 상태 유지
- 잠긴 계정 안내 메시지
- 은행 점검시간 안내 메시지
- 종료된 세션의 후속 입력 거부
- `FORCE_END_SESSION` 으로 현재 플로우 즉시 중단
