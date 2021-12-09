import asyncio
from typing import List

import aiohttp

from lms.services import ExternalAsyncRequestError


class AsyncOAuthHTTPService:
    def __init__(self, oauth2_token_service):
        self._oauth2_token_service = oauth2_token_service

    def request(
        self, method, urls: List[str], timeout=10, headers=None, **kwargs
    ) -> List[aiohttp.ClientResponse]:
        """
        Send access token-authenticated async requests with aiohttp to all `urls`.

        :param method: The HTTP method to use.

        :param urls:  All URLs to request

        :param timeout: How long (in seconds) to wait before raising an error
            for each of the requests.

        :param headers:  Headers to attach to all requests

        :param **kwargs: Any other keyword arguments will be passed directly to
            aiohttp.ClientSession().request():
            https://docs.aiohttp.org/en/stable/client_reference.html

        :raise OAuth2TokenError: if we don't have an access token for the user
        :raise ExternalRequestError: if something goes wrong with the HTTP
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

            raise ExternalRequestError("Blackboard async request failed") from err


def factory(_context, request):
    return AsyncOAuthHTTPService(request.find_service(name="oauth2_token"))
