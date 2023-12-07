from __future__ import annotations

from abc import ABC, abstractmethod

import httpx


class UCHttpClient(ABC):
    @abstractmethod
    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        pass

    @abstractmethod
    def post(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        content: str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        pass

    @abstractmethod
    def put(
        self,
        url: str,
        *,
        content: str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        pass

    @abstractmethod
    def delete(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        pass


class DefaultUCHttpClient(UCHttpClient):
    def __init__(self, *, base_url: str) -> None:
        self._client = httpx.Client(base_url=base_url)

    def get(self, url: str, *, params=None, headers=None) -> httpx.Response:
        return self._client.get(url, params=params, headers=headers)

    def post(
        self, url: str, *, params=None, content=None, headers=None
    ) -> httpx.Response:
        return self._client.post(url, params=params, content=content, headers=headers)

    def put(self, url: str, *, content=None, headers=None) -> httpx.Response:
        return self._client.put(url, content=content, headers=headers)

    def delete(self, url: str, *, params=None, headers=None) -> httpx.Response:
        return self._client.delete(url, params=params, headers=headers)


def create_default_uc_http_client(base_url: str) -> UCHttpClient:
    return DefaultUCHttpClient(base_url=base_url)


class UCHttpClientWithTimeout(DefaultUCHttpClient):
    def __init__(self, *, base_url: str, timeout: int = 5) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)


def create_uc_http_client_with_timeout(
    base_url: str, timeout=5
) -> UCHttpClientWithTimeout:
    return UCHttpClientWithTimeout(base_url=base_url, timeout=timeout)


# useful for debugging purposes, DO NOT USE for a production environment
class NoSSLVerificationHTTPClient(DefaultUCHttpClient):
    def __init__(self, *, base_url: str) -> None:
        self._client = httpx.Client(base_url=base_url, verify=False)


def create_no_ssl_http_client(base_url: str) -> NoSSLVerificationHTTPClient:
    return NoSSLVerificationHTTPClient(base_url=base_url)
