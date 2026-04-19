from __future__ import annotations

"""호환성용 transport gateway 별칭 모듈.

새 네임스페이스에서는 transport 기반 banking client 를
``banking.sdk.FileTransportBankSdk`` 로 다룬다.
기존 import 호환을 위해 이 모듈은 같은 구현체를 재노출한다.
"""

from .sdk import FileTransportBankGateway, FileTransportBankSdk

__all__ = ["FileTransportBankGateway", "FileTransportBankSdk"]
