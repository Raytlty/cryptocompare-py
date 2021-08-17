#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CryptoCompare API wrapper
"""
import os
import time
from collections import defaultdict
from datetime import datetime
from datetime import date
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from cryptocompare.base import Base


# API
_API_KEY_PARAMETER = ""
_URL_COIN_LIST = 'https://www.cryptocompare.com/api/data/coinlist'
_URL_PRICE_MULTI = 'https://min-api.cryptocompare.com/data/pricemulti'
_URL_PRICE_MULTI_FULL = 'https://min-api.cryptocompare.com/data/pricemultifull'
_URL_HIST_PRICE = 'https://min-api.cryptocompare.com/data/pricehistorical'
_URL_HIST_PRICE_DAY = 'https://min-api.cryptocompare.com/data/histoday'
_URL_HIST_PRICE_HOUR = 'https://min-api.cryptocompare.com/data/histohour'
_URL_HIST_PRICE_MINUTE = 'https://min-api.cryptocompare.com/data/histominute'
_URL_AVG = 'https://min-api.cryptocompare.com/data/generateAvg'
_URL_EXCHANGES = 'https://www.cryptocompare.com/api/data/exchanges'
_URL_PAIRS = 'https://min-api.cryptocompare.com/data/pair/mapping/exchange'

# TYPE
Timestamp = Union[datetime, date, int, float]


def _format_parameter(parameter: object) -> str:
    """
    Format the parameter depending on its type and return
    the string representation accepted by the API.
    :param parameter: parameter to format
    """
    if isinstance(parameter, list):
        return ','.join(parameter)

    else:
        return str(parameter)


class CryptoCompare(Base):

    @staticmethod
    def _format_parameter(param: object) -> str:
        """
        Format the parameter depending on its type and return
        the string representation accepted by the API.
        :param parameter: parameter to format
        """
        if isinstance(param, list):
            return ','.join(param)

        else:
            return str(param)

    def describe(self):
        return self.deep_extend(
            super(CryptoCompare, self).describe(),
            {
                'id': 'cryptocompare',
                'name': 'cryptocompare',
                'urls': {
                    'coin_list': _URL_COIN_LIST,
                    'avg': _URL_AVG,
                    'exchanges': _URL_EXCHANGES,
                    'pairs': _URL_PAIRS,
                    'price_multi': _URL_PRICE_MULTI,
                    'price_multi_full': _URL_PRICE_MULTI_FULL,
                    'history_price': _URL_HIST_PRICE,
                    'history_price_day': _URL_HIST_PRICE_DAY,
                    'history_price_hour': _URL_HIST_PRICE_HOUR,
                    'history_price_minute': _URL_HIST_PRICE_MINUTE,
                }
            })

    def sign(self, api, method='GET', params=None, headers=None, body=None):
        if api and not (api in self.urls):
            raise ValueError(self.id + ' api required')
        url = self.urls[api]
        if 'api_key' not in params:
            params['api_key'] = os.getenv('CRYPTOCOMPARE_API_KEY', '')
        if params:
            url += '?' + self.urlencode(params)
        return {
            'url': url,
            'method': method,
            'body': body,
            'headers': headers
        }

    def parse_full_price(
        self,
        raw_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        used = defaultdict(bool)
        prices = []
        for fsym, data in raw_data.items():
            for tsym, value in data.items():
                if used[(fsym, tsym)] is False:
                    used[(fsym, tsym)] = True
                    prices.append(self._parse_full_price(fsym, tsym, value))
        return prices

    def _parse_full_price(self, fsym, tsym, data) -> Dict[str, Any]:
        median = data.get('MEDIAN', 0)
        return {
            'from_symbol': fsym,
            'to_symbol': tsym,
            'price': data['PRICE'],
            'last_update': data['LASTUPDATE'],
            'info': {
                'type': data['TYPE'],
                'market': data['MARKET'],
                'from_symbol': data['FROMSYMBOL'],
                'to_symbol': data['TOSYMBOL'],
                'flags': data['FLAGS'],
                'last_update': data['LASTUPDATE'],
                'median': median,
                'last_volume': data['LASTVOLUME'],
                'last_volume_to': data['LASTVOLUMETO'],
                'last_trade_id': data['LASTTRADEID'],
                'volume_day': data['VOLUMEDAY'],
                'volume_day_to': data['VOLUMEDAYTO'],
                'volume_24hours': data['VOLUME24HOUR'],
                'volume_24hours_to': data['VOLUME24HOURTO'],
                'open_day': data['OPENDAY'],
                'high_day': data['HIGHDAY'],
                'low_day': data['LOWDAY'],
                'open_24hours': data['OPEN24HOUR'],
                'high_24hours': data['HIGH24HOUR'],
                'low_24hours': data['LOW24HOUR'],
                'last_market': data.get('LASTMARKET', ''),
                'volume_hour': data.get('VOLUMEHOUR', ''),
                'volume_hour_to': data.get('VOLUMEHOURTO', ''),
                'open_hour': data['OPENHOUR'],
                'high_hour': data['HIGHHOUR'],
                'low_hour': data['LOWHOUR'],
                'top_tier_volume_24hours': data.get('TOPTIERVOLUME24HOUR', ''),
                'top_tier_volume_24hours_to': data.get('TOPTIERVOLUME24HOURTO', ''),
                'change_24hours': data.get('CHANGE24HOUR', ''),
                'change_pct_24_hours': data.get('CHANGEPCT24HOUR', ''),
                'change_day': data.get('CHANGEDAY', ''),
                'change_pct_day': data.get('CHANGEPCTDAY', ''),
                'change_hour': data.get('CHANGEHOUR', ''),
                'change_pct_hour': data.get('CHANGEPCTHOUR', ''),
                'conversion_type': data['CONVERSIONTYPE'],
                'conversion_symbol': data['CONVERSIONSYMBOL'],
                'supply': data['SUPPLY'],
                'mk_tcap': data['MKTCAP'],
                'mk_tcap_penalty': data.get('MKTCAPPENALTY', ''),
                'total_volume_24hours': data.get('TOTALVOLUME24H', ''),
                'total_volume_24hours_to': data.get('TOTALVOLUME24HTO', ''),
                'total_top_tier_volume_24hours': data.get('TOTALTOPTIERVOLUME24H', ''),
                'total_top_tier_volume_24hours_to': data.get('TOTALTOPTIERVOLUME24HTO', '')
            }
        }

    def parse_single_price(self, raw_data):
        prices = []
        for fsym, data in raw_data.items():
            for tsym, price in data.items():
                prices.append(
                    {
                        'from_symbol': fsym,
                        'to_symbol': tsym,
                        'price': price
                    }
                )
        return prices

    def get_coin_list(self, formated: bool = False) -> Union[Dict, List, None]:
        """
        Get the coin list (all available coins).
        :param format: format as python list (default: False)
        :returns: dict or list of available coins
        """
        resp = self.fetch2('coin_list')
        coin_list = []
        for k, v in resp.get('Data', {}).items():
            assert k == v['Symbol']
            coin_list.append(
                {
                    'symbol': k,
                    'name': v['Name'],
                    'coin_name': v['CoinName'],
                    'full_name': v['FullName'],
                    'description': v['Description']
                }
            )
        return coin_list

    def get_price(
        self,
        from_symbols: Union[str, List],
        to_symbols: Union[str, List],
        exchange: Optional[str] = None,
        full: bool = False
    ) -> Optional[Dict]:
        """
        Get the currencyent price of a coin in a given currency.
        :param from_symbols: symbolic name of the coin (e.g. BTC)
        :param to_symbols: short hand description of the currency (e.g. EUR)
        :param full: full response or just the price (default: False)
        :returns: list of dict of coin and currency price pairs
        """
        params = {
            'fsyms': self._format_parameter(from_symbols),
            'tsyms': self._format_parameter(to_symbols)
        }
        if exchange:
            params['e'] = exchange
        if full:
            resp = self.fetch2('price_multi_full', params=params)
            return self.parse_full_price(resp.get('RAW', {}))
        else:
            resp = self.fetch2('price_multi', params=params)
            return self.parse_single_price(resp)
