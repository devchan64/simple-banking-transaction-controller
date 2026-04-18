from __future__ import annotations

import json
from pathlib import Path

from banking import BankRequest, BankResponse

from tests.support.process_support import ModuleProcessSupport


class BankingTransportSupport(ModuleProcessSupport):
    def write_bank_request(self, transport_root: Path, request: BankRequest) -> None:
        requests_dir = transport_root / "requests"
        requests_dir.mkdir(parents=True, exist_ok=True)
        (requests_dir / f"{request.request_id}.json").write_text(
            json.dumps(request.model_dump(mode="json"), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def wait_for_bank_response(
        self,
        transport_root: Path,
        request_id: str,
        timeout_seconds: float = 3.0,
    ) -> BankResponse:
        response_path = transport_root / "responses" / f"{request_id}.json"
        self.wait_for_file(response_path, timeout_seconds=timeout_seconds)
        return BankResponse.model_validate(
            json.loads(response_path.read_text(encoding="utf-8"))
        )
