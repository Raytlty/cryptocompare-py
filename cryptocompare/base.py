#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CryptoCompare Base wrapper
"""
import json
import time
from collections import defaultdict
from collections import OrderedDict
from requests import Session
from requests.utils import default_user_agent
from requests.exceptions import HTTPError
from requests.exceptions import Timeout
from requests.exceptions import TooManyRedirects
from requests.exceptions import RequestException
from requests.exceptions import ConnectionError as requestsConnectionError
from ssl import SSLError
from uuid import uuid4
from urllib import parse as _urlencode  # Python3

from cryptocompare.exceptions import DomainError
from cryptocompare.exceptions import NetworkError
from cryptocompare.exceptions import RateLimitExceeded
from cryptocompare.exceptions import RequestTimeout


class Base:
    """base request client"""
    id = None
    name = None
    session = None
    proxy = ''
    proxies = None
    userAgent = None
    headers = None
    quoteJsonNumbers = True
    verify = True
    userAgents = {
        'chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/62.0.3202.94 Safari/537.36',

        'chrome39': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36'
        ' (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    }
    symbols = None
    lastRestRequestTimestamp = 0
    origin = None
    timeout = 10000
    httpExceptions = {
        '429': RateLimitExceeded,
        '408': RequestTimeout,
        '504': RequestTimeout,
    }

    def __init__(self, config=None):
        if config is None:
            config = dict()
        self.origin = self.uuid()
        self.headers = dict() if self.headers is None else self.headers
        self.userAgent = default_user_agent()
        settings = self.deep_extend(self.describe(), config)

        for key in settings:
            if hasattr(self, key) and isinstance(getattr(self, key), dict):
                v = self.deep_extend(getattr(self, key), settings[key])
                setattr(self, key, v)
            else:
                setattr(self, key, settings[key])
        self.session = self.session if self.session else Session()

    def __del__(self):
        if self.session:
            self.session.close()

    def describe(self):
        return {}

    def prepare_request_headers(self, headers=None):
        headers = headers or {}
        headers.update(self.headers)
        if self.userAgent:
            if type(self.userAgent) is str:
                headers.update({'User-Agent': self.userAgent})
            elif (
                type(self.userAgent) is dict) and\
                    ('User-Agent' in self.userAgent):
                headers.update(self.userAgent)
        if self.proxy:
            headers.update({'Origin': self.origin})
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

    def parse_json(self, http_response):
        try:
            if self.is_json_encoded_object(http_response):
                return self.on_json_response(http_response)
        except ValueError:
            pass

    def on_json_response(self, response_body):
        if self.quoteJsonNumbers:
            return json.loads(response_body, parse_float=str, parse_int=str)
        else:
            return json.loads(response_body)

    def sign(self, api, method='GET', params=None, headers=None, body=None):
        raise NotImplementedError(self.id + ' sign() pure method must '
                                  'be redefined in derived classes')

    def fetch2(self, api, method='GET', params=None, headers=None, body=None):
        """A better wrapper over request for deferred signing"""
        if params is None:
            params = dict()
        self.lastRestRequestTimestamp = self.milliseconds()
        request = self.sign(api, method, params, headers, body)
        return self.fetch(
            request['url'],
            request['method'],
            request['headers'],
            request['body']
        )

    def fetch(self, url, method='GET', headers=None, body=None):
        request_headers = self.prepare_request_headers(headers)
        url = self.proxy + url
        if isinstance(body, str):
            body = body.encode()
        self.session.cookies.clear()
        http_response = None
        http_status_code = None
        http_status_text = None
        json_response = None
        try:
            response = self.session.request(
                method,
                url,
                data=body,
                headers=request_headers,
                timeout=int(self.timeout / 1000),
                proxies=self.proxies,
                verify=self.verify
            )
            # does not try to detect encoding
            response.encoding = 'utf-8'
            headers = response.headers
            http_status_code = response.status_code
            http_status_text = response.reason
            http_response = response.text.strip()
            json_response = self.parse_json(http_response)
            response.raise_for_status()

        except Timeout as e:
            details = ' '.join([self.id, method, url])
            raise DomainError(details) from e

        except TooManyRedirects as e:
            details = ' '.join([self.id, method, url])
            raise DomainError(details) from e

        except SSLError as e:
            details = ' '.join([self.id, method, url])
            raise DomainError(details) from e

        except HTTPError as e:
            details = ' '.join([self.id, method, url])
            self.handle_http_status_code(http_status_code,
                                         http_status_text,
                                         url,
                                         method,
                                         http_response)
            raise DomainError(details) from e

        except requestsConnectionError as e:
            error_string = str(e)
            details = ' '.join([self.id, method, url])
            if 'Read timed out' in error_string:
                raise RequestTimeout(details) from e
            else:
                raise NetworkError(details) from e

        except ConnectionResetError as e:
            error_string = str(e)
            details = ' '.join([self.id, method, url])
            raise NetworkError(details) from e

        except RequestException as e:  # base exception class
            error_string = str(e)
            details = ' '.join([self.id, method, url])
            if any(
                    x in error_string for x in
                    [
                        'ECONNRESET',
                        'Connection aborted',
                        'Connection broken'
                    ]
            ):
                raise NetworkError(details) from e
            else:
                raise DomainError(details) from e

        if json_response is not None:
            return json_response
        elif self.is_text_response(headers):
            return http_response
        else:
            return response.content

    @staticmethod
    def uuid():
        return uuid4().hex

    @staticmethod
    def milliseconds():
        return int(time.time() * 1000)

    @staticmethod
    def seconds():
        return int(time.time())

    @staticmethod
    def is_text_response(headers):
        content_type = headers.get('Content-Type', '')
        return content_type.startswith('application/json') or\
            content_type.startswith('text/')

    @staticmethod
    def is_json_encoded_object(obj):
        return (
            isinstance(obj, str) and
            (len(obj) >= 2) and
            ((obj[0] == '{') or
             (obj[0] == '['))
        )

    @staticmethod
    def deep_extend(*args):
        result = defaultdict(dict)
        for arg in args:
            if not arg:
                continue
            if isinstance(arg, dict):
                for k, v in arg.items():
                    result[k] = Base.deep_extend(
                        result[k] if k in result else [],
                        v
                    )
            else:
                result = arg
        return result

    @staticmethod
    def strip(string):
        return string.strip()

    @staticmethod
    def keysort(d):
        return OrderedDict(sorted(d.items(), key=lambda t: t[0]))

    @staticmethod
    def extend(*args):
        if args is not None:
            result = None
            if type(args[0]) is OrderedDict:
                result = OrderedDict()
            else:
                result = {}
            for arg in args:
                result.update(arg)
            return result
        return {}

    @staticmethod
    def urlencode(params={}, doseq=False):
        for key, value in params.items():
            if isinstance(value, bool):
                params[key] = 'true' if value else 'false'
        return _urlencode.urlencode(params, doseq)
