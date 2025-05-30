import asyncio
import json

import aiohttp

from lms.services import ExternalAsyncRequestError


class AsyncOAuthHTTPService:
    def __init__(self, oauth2_token_service):
        self._oauth2_token_service = oauth2_token_service

    def request(
        self, method, urls: list[str], timeout=10, headers=None, **kwargs
    ) -> list[aiohttp.ClientResponse]:
        r"""
        Send access token-authenticated async requests with aiohttp to all `urls`.

        :param method: The HTTP method to use.
        :param urls:  All URLs to request
        :param timeout: How long (in seconds) to wait before raising an error
            for each of the requests.
        :param headers:  Headers to attach to all requests
        :param \**kwargs: Any other keyword arguments will be passed directly to
            aiohttp.ClientSession().request():
            https://docs.aiohttp.org/en/stable/client_reference.html

        :raise OAuth2TokenError: if we don't have an access token for the user
        :raise ExternalAsyncRequestError: if something goes wrong with the HTTP
            request
        """
        headers = headers or {}

        access_token = self._oauth2_token_service.get().access_token
        headers["Authorization"] = f"Bearer {access_token}"
        return asyncio.run(
            _prepare_requests(method, urls, timeout=timeout, headers=headers, **kwargs)
        )


async def _async_request(aio_session, method, url, **kwargs):
    async with aio_session.request(method, url, **kwargs) as response:
        # Calling `.text()` here caches the result in `response` but is still behind a coroutine.
        # We assign it to another response attribute for it to be
        # available in a sync context without needing to start coroutine.
        response.sync_text = await response.text()
        # For json we want to emulate the behaviour of the sync version, calling json might raise if text is not valid json
        response.json = lambda: json.loads(response.sync_text)
        return response


async def _prepare_requests(method, urls, **kwargs):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            task = asyncio.create_task(
                _async_request(
                    session,
                    method,
                    url,
                    **kwargs,
                )
            )
            tasks.append(task)
        try:
            return await asyncio.gather(*tasks, return_exceptions=False)
        except aiohttp.ClientError as err:
            for task in tasks:
                task.cancel()

            raise ExternalAsyncRequestError() from err  # noqa: RSE102


def factory(_context, request):
    return AsyncOAuthHTTPService(request.find_service(name="oauth2_token"))
