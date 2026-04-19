# 문서 개선 메모

## 목적

이 문서는 현재 저장소 문서에 아직 충분히 반영되지 않은 개선 포인트를 정리한다.

기준 참고 커밋:

- `49d74f5b658bdd14a19caab97c1d99a0288afcee`

위 커밋은 새로운 SSOT 문서를 추가했다기보다,
코드 내부 주석과 독스트링으로 세션 경계, transport 어댑터, 테스트 책임 분리에 대한
온보딩 메모를 보강한 변경에 가깝다.

따라서 아래 항목은 "현재 코드가 이미 암시하고 있지만 문서에는 충분히 올라오지 않은 내용"을
문서 관점에서 다시 정리한 목록이다.

## 1. 세션 경계 문서 보강

현재 세션 관련 구현은 두 갈래로 나뉘어 있다.

- `src/banking/session.py`
  - 세션 토큰 발급 이력을 남긴다
- `src/controller/session_store.py`
  - 현재 활성 세션 스냅샷과 상태 전이를 저장한다

하지만 SSOT 문서에는 이 분리가 왜 생겼는지,
그리고 어떤 점이 아직 미완성인지가 충분히 드러나지 않는다.

문서에 보강되면 좋은 내용:

- 세션 토큰 발급 이력과 활성 세션 상태가 서로 다른 저장소로 나뉜 현재 이유
- 현재 구조가 완성된 세션 시스템이 아니라 과도기 구현이라는 설명
- 아직 비어 있는 세션 정책 범위
  - 만료
  - 갱신(refresh)
  - 무효화
  - 활성 세션 정리(cleanup)
  - 세션 메타데이터 관리
- 장기적으로 세션의 단일 진실 원천을 어디에 둘지에 대한 결정 필요성

추천 반영 위치:

- `docs/ssot/controller.md`
- `docs/ssot/persistence.md`
- `docs/ssot/persistence-json.md`

## 2. Controller 와 Session 책임 분리 설명 추가

`Controller` 는 현재 ATM 절차의 핵심 상태머신이지만,
세션 설계까지 완결된 계층은 아니다.

문서에 보강되면 좋은 내용:

- `Controller` 가 책임지는 범위
  - 명령 검증
  - 상태 전이
  - 결과 생성
- `Controller` 가 아직 책임지지 않는 범위
  - 세션 만료 정책
  - 세션 갱신 정책
  - 추가 인증 정책
  - 세션 생명주기 전체 orchestration
- 현재 서버 조립 계층과 controller 사이에서 세션 책임이 완전히 정리되지 않았다는 설명

이 내용이 빠져 있으면 문서를 읽는 사람이
"세션 토큰이 이미 있으니 전체 세션 시스템도 완성돼 있겠지"라고 오해하기 쉽다.

추천 반영 위치:

- `docs/ssot/controller.md`

## 3. Transport 테스트 책임 분리 필요성 문서화

현재 `tests/transport/test_transport_spec.py` 는
transport 자체 계약 검증과 서버 경계 검토가 함께 섞여 있다.

또 `tests/transport/worker_process.py` 는
실제 서버 엔트리포인트가 아니라 요청 하나만 처리하는 과도기 worker 로 남아 있다.

문서에 보강되면 좋은 내용:

- transport 단일 계약 테스트와 서버 통합 테스트를 구분해야 한다는 점
- transport 테스트가 확인해야 할 최소 범위
  - request 기록
  - response 읽기
  - request/response 연결
  - payload 직렬화 유지
- 서버 기반 검증이 확인해야 할 범위
  - 서버 프로세스가 transport 경계를 실제로 읽고 쓰는지
  - 성공/실패 응답 구조가 계약에 맞는지
- 현재 worker helper 는 과도기 산출물이라는 설명
- 장기적으로는 실제 server entry 와 lifecycle 을 더 직접 재사용하는 방향이 자연스럽다는 점

추천 반영 위치:

- `docs/ssot/transport.md`
- 필요 시 `tests/controller/test_controller_spec.md`

## 4. README 수준의 온보딩 설명 보강

현재 `README.md` 는 실행 흐름과 계층 개요는 잘 설명하지만,
다음과 같은 "현재 구조의 미완성 지점"은 거의 드러나지 않는다.

- 세션 경계가 history store 와 active session store 로 분리되어 있는 점
- transport 테스트가 아직 과도기 구조를 포함하고 있다는 점

README 에 이 모든 세부사항을 길게 넣을 필요는 없지만,
처음 들어오는 사람이 큰 오해를 하지 않도록 짧은 주석 수준의 안내는 있으면 좋다.

추천 반영 방식:

- `현재 한계` 또는 `설계 메모` 섹션 1개 추가
- 자세한 내용은 SSOT 문서 경로로 링크

## 5. 문서화 우선순위 제안

우선순위가 높은 순서로 정리하면 다음과 같다.

1. `docs/ssot/controller.md` 에 세션 책임의 현재 한계 반영
2. `docs/ssot/persistence*.md` 에 history store / active session store 분리 설명 반영
3. `docs/ssot/transport.md` 에 transport 테스트와 worker helper 의 과도기성 반영
4. `README.md` 에 짧은 온보딩 경고 또는 설계 메모 추가

## 6. 문서 작성 원칙

이 개선 항목들을 실제 문서에 반영할 때는 다음 원칙을 유지하는 편이 좋다.

- 현재 동작과 미래 설계 희망을 섞지 않는다
- "이미 지원하는 것"과 "아직 비어 있는 것"을 명확히 구분한다
- 과도기 구조라는 설명은 남기되,
  현재 구현의 실제 역할과 검증 가능한 가치는 함께 적는다
- README 에는 요약만 두고,
  상세 설명은 SSOT 문서로 올린다
