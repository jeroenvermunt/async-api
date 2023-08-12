
import json
import aiohttp
import asyncio
import urllib
from pysdk.metaclass import ApiMetaclass
from pprint import pprint


class MaxRetriesError(Exception):
    pass


class ApiBase(metaclass=ApiMetaclass):
    """base class for async api calls

    feature: add decorator which calls the correct endpoint
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 10,
        retry_delay: int = 1,
        verbose: bool = True,
        **client_kwargs
    ):

        self.n_retries = 0
        self.max_retries = max_retries
        self.verbose = verbose
        self.session = None
        self.open_contexts = 0
        self.retry_delay = retry_delay

        timeout = aiohttp.ClientTimeout(
                # default value is 5 minutes, set to `None` for unlimited
                total=timeout,
                # How long to wait before an open socket allowed to connect
                sock_connect=timeout,
                # How long to wait with no data being read before timing out
                sock_read=timeout
            )

        self.client_args = dict(
            trust_env=True,
            timeout=timeout,
            **client_kwargs
        )

    def __enter__(self):
        raise NotImplementedError('Use async context manager instead')

    def __exit__(self, exc_type, exc, tb):
        raise NotImplementedError('Use async context manager instead')
    
    async def __aenter__(self):
        self.open_contexts = self.open_contexts + 1
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(**self.client_args)
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        self.open_contexts = self.open_contexts - 1
        if self.open_contexts == 0:
            await self.session.close()

    async def handle_error(self, e, request_func, *args, **kwargs):

        # check exception type
        match e.__class__:

            case aiohttp.ClientConnectorCertificateError:
                # raise certificate error, no use to retry
                raise e

            case aiohttp.ClientError:
                pass
            case asyncio.TimeoutError:
                pass

            # if no match (unexpected), raise the exception
            case _:
                raise e

        if self.n_retries < self.max_retries:
            self.n_retries += 1
            await asyncio.sleep(self.retry_delay)
            return await request_func(*args, **kwargs)

        else:
            raise MaxRetriesError('Max retries reached')     

    async def get(self, url: str, params: dict = None, **kwargs):
        """send a "batteries included" async get request to the api,

        performs:
            - url encoding
            - retries
            - error handling
            - response parsing
            - opens/closes a session if not already open, 
              only use when sending one request at a time 
              with this class

        Args:
            url: Url to call
            params: Query parameters to be added to the url 

        Returns:
            output of self.parse_response: 
        """        

        # encode query parameters into the url
        if params:
            query_string = urllib.parse.urlencode(params)

            if '?' in url:
                url += '&' + query_string
            else:
                url += '?' + query_string

        # open a session if not already open and send request
        try:
            async with (
                self as s,
                s.get(url, headers=self.headers) as r,
            ):

                return await self.parse_response(r, **kwargs)

        # catch all exceptions and parse in handle_error
        except Exception as e: 
            return await self.handle_error(e, self.get, url, **kwargs)

    async def post(self, url, data: dict, **kwargs):

        if self.verbose:
            print(f'Calling post method')
            print(f'Url: {url}')
            pprint(data)

        try:
            async with (
                self as s,
                s.post(url, headers=self.headers, data=json.dumps(data)) as r,
            ):

                return await self.parse_response(r, **kwargs)

        except Exception as e: 
            return await self.handle_error(e, self.get, url, **kwargs)

    async def put(self, url, data: dict, **kwargs):

        try:
            async with (
                self as s,
                s.put(url, headers=self.headers, data=json.dumps(data)) as r,
            ):

                return await self.parse_response(r, **kwargs)

        except Exception as e: 
            return await self.handle_error(e, self.get, url, **kwargs)

    async def parse_response(self, response, return_type=None):
        """_summary_

        Args:
            response (_type_): _description_
            return_type (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """        

        if not return_type:
            return_type = self.return_type

        if self.verbose:
            print(response.status)
            print(response.reason)

        if return_type == 'json':
            print('Returning response as json')
            return await response.json()

        elif return_type == 'image':
            print('Returning response as image')
            return await response.read()

        if self.verbose:
            print('Returning response as aiohttp response object')

        return response
