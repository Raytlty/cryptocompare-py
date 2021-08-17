#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseError(Exception):
    pass


class DomainError(BaseError):
    pass


class BadRequest(BaseError):
    pass


class BadSymbol(BadRequest):
    pass


class NetworkError(BaseError):
    pass


class DDoSProtection(NetworkError):
    pass


class RateLimitExceeded(DDoSProtection):
    pass


class RequestTimeout(NetworkError):
    pass


__all__ = [
    'BaseError',
    'DomainError',
    'BadRequest',
    'BadSymbol',
    'NetworkError',
    'DDoSProtection',
    'RateLimitExceeded',
    'RequestTimeout'
]

