# Prompt Adapter SSOT

## 목적

- CLI 도구
- controller 검증 지원
- 테스트 입력 실행

## 성격

- 테스트용 보조 도구
- 가벼운 실행 도구
- 문자열 기반 도구

## 방식

- prompt 출력
- 사용자 입력 수집
- 문자열 -> `SessionCommand`
- 결과 출력

## 책임

- CLI 입력 받기
- command 변환
- transport 호출
- 결과 표시

## 구현 키워드

- cli tool
- test helper
- lightweight
- interactive input
- command conversion


## 한 줄 정의

Prompt Adapter는 controller 테스트를 위해 사용하는 가벼운 CLI 보조 도구이다.
