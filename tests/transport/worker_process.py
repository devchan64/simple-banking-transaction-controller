from __future__ import annotations

"""transport 스펙에서 남아 있는 과도기용 worker 프로세스.

배경
----
- 이 헬퍼의 첫 버전은 실제 controller를 실행하지 않았다.
  별도 프로세스에서 성공 응답이나 에러 응답을 흉내 낼 수 있도록
  인메모리 ``WorkerController`` 와 mode 플래그를 사용했다.
- 이후 transport 스펙을 실제 controller/banking 경계 쪽으로 옮기면서
  ``controller.server.build_controller()`` 를 호출하도록 바뀌었다.
  하지만 그 전환이 충분히 끝나지 않아, 실제 controller 서버 엔트리포인트가
  아니라 한 번만 요청을 처리하는 얇은 worker 형태가 그대로 남아 있다.

현재 모양이 어색한 이유
----------------------
그래서 이 파일은 과도기 산출물에 가깝다.
현재의 "transport 파일을 대상으로 controller 서버를 실행한다"는 구조보다,
이전의 "헬퍼 프로세스를 띄워 요청 하나만 처리한다"는 구조를 더 많이 반영한다.
지금 기준으로 보면 transport 스펙에 별도 worker가 꼭 필요한 상태도 아니다.

그 결과 transport 테스트는 다음이 섞인 형태가 된다.
- request/response 파일 transport 자체는 실제 구현을 사용한다
- controller 생성도 실제 구현을 사용한다
- banking transport 경계도 실제 구현을 사용한다
- 하지만 서버 루프와 프로세스 엔트리는 여기서 다시 구현하고 있다

앞으로 반영되면 좋은 점
----------------------
transport 스펙이 서버 기반 설계와 완전히 맞춰진다면,
이 헬퍼는 사라지는 쪽이 더 자연스럽다.
정말 별도 프로세스 래퍼가 필요할 때만, 실제 controller 서버 모듈을 감싸는
아주 작은 수준으로 남기는 편이 낫다.

아직 이 파일에 충분히 반영되지 않은 서버 기준 동작은 다음과 같다.
- 실제 실행 경로에서 사용하는 동일한 모듈 엔트리를 시작할 것
- ``controller.server._process_next_request()`` 와 같은 방식으로 request 파일을 순회할 것
- 여기서 ``wait_for_request() -> handle() -> write_response()`` 흐름을 중복하지 말고
  polling/lifecycle 동작을 한 곳에 모을 것
- 실제 서버와 같은 로깅 및 에러 매핑 경로를 공유할 것
- transport 자체 검증과 controller 통합 검증이 서로 다른 관심사임을 더 분명히 드러낼 것
"""

import sys
from pathlib import Path

from controller.server import build_controller
from transport import FileTransport, SessionResponseEnvelope


def main() -> int:
    """transport 통합 스펙을 위해 대기 중인 요청 하나만 처리하는 과도기 진입점."""
    transport_root = Path(sys.argv[1])
    request_id = sys.argv[2]
    runtime_root = Path(sys.argv[3])
    banking_root = Path(sys.argv[4])

    transport = FileTransport(
        transport_root=transport_root,
        poll_interval_seconds=0.01,
        timeout_seconds=3.0,
    )
    controller = build_controller(runtime_root, banking_root)
    request = transport.wait_for_request(request_id)

    try:
        # controller.server 일부를 흉내 내지만, 여기서는 요청 하나만 처리한다.
        result = controller.handle(request.command)
        response = SessionResponseEnvelope(
            request_id=request.request_id,
            result=result.model_dump(mode="json"),
        )
    except Exception as exc:
        response = SessionResponseEnvelope(
            request_id=request.request_id,
            error_code=type(exc).__name__,
            error_message=str(exc),
        )

    transport.write_response(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
