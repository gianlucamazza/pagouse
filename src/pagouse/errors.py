"""Structured errors for the CLI / MCP JSON envelope."""

from __future__ import annotations

__all__ = [
    "BadArg",
    "BadConfig",
    "ContextNotFound",
    "CredentialFieldInvalid",
    "CredentialNotFound",
    "CredentialOriginMismatch",
    "Denied",
    "IpcFailed",
    "NoSession",
    "NoTab",
    "OriginChanged",
    "PagouseError",
    "Readonly",
    "RestrictedPage",
    "SecretProviderUnavailable",
    "SecretResolutionFailed",
    "SessionRecoveryFailed",
    "SessionStartFailed",
    "StaleMetadata",
    "StaleRef",
    "Unsupported",
    "WaitTimeout",
    "WebDriverError",
    "WebDriverUnavailable",
]


class PagouseError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class NoSession(PagouseError):
    def __init__(self, message: str = "managed browser session is not connected") -> None:
        super().__init__("no_session", message)


class NoTab(PagouseError):
    def __init__(self, tab_id: int | None = None) -> None:
        detail = "no usable tab" if tab_id is None else f"tab {tab_id} not found"
        super().__init__("no_tab", detail)
        self.tab_id = tab_id


class StaleRef(PagouseError):
    def __init__(self, ref: str) -> None:
        super().__init__("stale_ref", f"{ref} is no longer in the document")
        self.ref = ref


class IpcFailed(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("ipc_failed", detail)


class RestrictedPage(PagouseError):
    """Chromium forbids scripting this page (Web Store gallery, chrome pages)."""

    def __init__(self, detail: str) -> None:
        super().__init__("restricted_page", detail)


class Readonly(PagouseError):
    def __init__(self, message: str = "input disabled (readonly)") -> None:
        super().__init__("readonly", message)


class Denied(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("denied", detail)


class OriginChanged(PagouseError):
    def __init__(self, detail: str = "tab origin changed during the action") -> None:
        super().__init__("origin_changed", detail)


class BadConfig(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("bad_config", detail)


class BadArg(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("bad_arg", detail)


class WaitTimeout(PagouseError):
    def __init__(self, detail: str = "wait timed out") -> None:
        super().__init__("wait_timeout", detail)


class Unsupported(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("unsupported", detail)


class WebDriverError(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("webdriver_error", detail)


class WebDriverUnavailable(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("webdriver_unavailable", detail)


class SessionStartFailed(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("session_start_failed", detail)


class SessionRecoveryFailed(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("session_recovery_failed", detail)


class StaleMetadata(PagouseError):
    def __init__(self, detail: str = "managed browser metadata is stale") -> None:
        super().__init__("stale_metadata", detail)


class ContextNotFound(PagouseError):
    def __init__(self, context: str) -> None:
        super().__init__("context_not_found", f"context {context} not found")


class CredentialNotFound(PagouseError):
    def __init__(self, handle: str) -> None:
        super().__init__("credential_not_found", f"credential handle {handle} is not configured")


class CredentialFieldInvalid(PagouseError):
    def __init__(self, field: str) -> None:
        super().__init__("credential_field_invalid", f"credential field is not allowed: {field}")


class CredentialOriginMismatch(PagouseError):
    def __init__(self, origin: str) -> None:
        super().__init__("credential_origin_mismatch", f"credential is not allowed on {origin}")


class SecretProviderUnavailable(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("secret_provider_unavailable", detail)


class SecretResolutionFailed(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("secret_resolution_failed", detail)
