"""OAuth2 grants."""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional

from ._misc import CLIENT_ID, CLIENT_SECRET, SCOPE

__all__ = [
    "BaseGrant",
    "AuthorizationCodeGrant",
    "ClientCredentialsGrant",
    "RefreshTokenGrant",
]


class BaseGrant:
    """Base grant class. Not intended for direct use, use inherited classes.

    :param parameters: Grant parameters.
    """

    def __init__(self, parameters: Mapping[str, str]) -> None:
        self._params = {
            key: value
            for key, value in parameters.items()
            if key != "self" and not key.startswith("__") and value is not None
        }

    def __repr__(self) -> str:
        client_id = self._params.get("client_id")
        return f"<{type(self).__name__} client_id={repr(client_id)}>"

    def _set_grant_type(self, grant_type: str) -> None:
        self._params["grant_type"] = grant_type

    def get_refresh_token_grant(self, refresh_token: str) -> RefreshTokenGrant:
        """Get a new RefreshTokenGrant from the current grant and refresh_token."""
        return RefreshTokenGrant(
            refresh_token,
            self._params["client_id"],
            self._params["client_secret"],
        )

    @property
    def parameters(self) -> MappingProxyType[str, str]:
        """Grant parameters."""
        return MappingProxyType(self._params)


class AuthorizationCodeGrant(BaseGrant):
    """Authorization code grant.

    The class in derived from :class:`BaseGrant`, shares all parent’s attributes and
    methods.

    :param code: Authorization code.
    :param redirect_uri: Redirect URL used with authorization.
    :param client_id: App client ID.
    :param client_secret: App client secret.
    :param scope: Scopes space separated.
    """

    def __init__(
        self,
        code: str,
        client_id: str = CLIENT_ID,
        client_secret: str = CLIENT_SECRET,
        redirect_uri: Optional[str] = None,
        scope: Optional[str] = SCOPE,
    ) -> None:
        super().__init__(locals())
        self._set_grant_type("authorization_code")


class ClientCredentialsGrant(BaseGrant):
    """Client credentials grant.

    The class in derived from :class:`BaseGrant`, shares all parent’s attributes and
    methods.

    :param username: User address email.
    :param password: User password.
    :param client_id: App client ID.
    :param client_secret: App client secret.
    :param scope: Scopes space separated.
    """

    def __init__(
        self,
        username: str,
        password: str,
        client_id: str = CLIENT_ID,
        client_secret: str = CLIENT_SECRET,
        scope: Optional[str] = SCOPE,
    ) -> None:
        super().__init__(locals())
        self._set_grant_type("password")


class RefreshTokenGrant(BaseGrant):
    """Refresh token grant.

    The class in derived from :class:`BaseGrant`, shares all parent’s attributes and
    methods.

    :param refresh_token: The refresh token.
    :param client_id: App client ID.
    :param client_secret: App client secret.
    """

    def __init__(
        self,
        refresh_token: str,
        client_id: str = CLIENT_ID,
        client_secret: str = CLIENT_SECRET,
    ):
        super().__init__(locals())
        self._set_grant_type("refresh_token")
