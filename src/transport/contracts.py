from __future__ import annotations

from enum import StrEnum


TRANSPORT_ROOT_ENV = "BANKING_TRANSPORT_ROOT"
TRANSPORT_FILE_SUFFIX = ".json"


class TransportDirectoryName(StrEnum):
    REQUESTS = "requests"
    RESPONSES = "responses"


class WorkerMode(StrEnum):
    ERROR = "error"
    SUCCESS = "success"
