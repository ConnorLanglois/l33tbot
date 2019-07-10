from collections import namedtuple
from enum import Enum
from socketclusterclient import Socketcluster
from threading import Thread
from time import sleep

import numpy as np
import pandas as pd
import requests

credentials = namedtuple('credentials', ('api', 'secret', 'endpoint'))
connection = namedtuple('connection', ('hostname', 'port', 'secure'))
alerts = namedtuple('alerts', ('open_alerts', 'alert_history'))

class OrderTypeId(Enum):
	BUY = 1,
	SELL = 2

class PriceTypeId(Enum):
	LIMIT = 3,
	STOP_LIMIT = 6,
	MARGIN_LIMIT = 8,
	MARGIN_STOP_LIMIT = 9

class Account:
	def __init__(self, api, secret, endpoint, uri):
		self.api = api
		self.secret = secret
		self.endpoint = endpoint
		self.uri = uri

class Coinigy:
	def __init__(self, acct):
		self.api = acct.api
		self.secret = acct.secret
		self.endpoint = acct.endpoint
		self.uri = acct.uri

		self.socket = Socketcluster.socket(self.uri)

		self.socket.setBasicListener(self.on_connect, self.on_disconnect, self.on_connect_error)
		self.socket.setAuthenticationListener(self.on_set_authentication, self.on_authentication)
		self.socket.setdelay(3)

	def connect(self, on_authenticated):
		self.on_authenticated = on_authenticated

		Thread(target=self.socket.connect).start()

	def subscribe_ticker(self, handler):
		self.subscribe('TICKER', handler)

	def subscribe_news(self, handler):
		self.subscribe('NEWS', handler)

	def subscribe_chat(self, handler):
		self.subscribe('CHATMSG', handler)

	def subscribe_notifications(self, handler):
		self.subscribe('NOTIFICATION', handler)

	def subscribe_favorites(self, handler):
		self.subscribe('FAVORITES', handler)

	def subscribe_block(self, market, handler):
		self.subscribe(f'BLOCK-{market}', handler)

	def subscribe_trades(self, exchange_code, market, handler):
		self.subscribe(f'TRADE-{exchange_code}--{market.split("/")[0]}--{market.split("/")[1]}', handler)

	def subscribe_orders(self, exchange_code, market, handler):
		self.subscribe(f'ORDER-{exchange_code}--{market.split("/")[0]}--{market.split("/")[1]}', handler)

	def subscribe(self, channelName, handler):
		def decorate_handler(key, objects):
			if isinstance(objects, list):
				for obj in objects:
					handler(namedtuple('Obj', obj.keys())(*obj.values()))
			else:
				handler(namedtuple('Obj', objects.keys())(*objects.values()))

		self.socket.subscribe(channelName)
		self.socket.onchannel(channelName, decorate_handler)

	def on_connect(self, socket):
		print('Connected')

	def on_disconnect(self, socket):
		print('Disconnected')

	def on_connect_error(self, socket, error):
		print('Connection error: ', error)

	def on_set_authentication(self, socket, token):
		print('Authentication token received:', token)
		self.socket.setAuthtoken(token)

	def on_authentication(self, socket, is_authenticated):
		print('Is authenticated:', is_authenticated)

		def ack(event, error, data):
			print('Authenticated')
			self.on_authenticated()

		self.socket.emitack('auth', {
			'apiKey': self.api,
			'apiSecret': self.secret
		}, ack)

	def request(self, method, query=None, json=True, **args):
		"""
		Generic interface to REST api
		:param method:  query name
		:param query:   dictionary of inputs
		:param json:	if True return the raw results in json format
		:param args:	keyword arguments added to the payload
		:return:
		"""
		url = '{endpoint}/{method}'.format(endpoint=self.endpoint, method=method)
		payload = {
			'X-API-KEY': self.api,
			'X-API-SECRET': self.secret
		}

		payload.update(**args)

		if query is not None:
			payload.update(query)

		r = requests.post(url, data=payload)

		if 'error' in list(r.json().keys()):
			print(r.json()['error'])
			return

		if json:
			return r.json()

		return pd.DataFrame(r.json()['data'])

	def data(self, exchange, market, data_type):
		"""
		Common wrapper for data related queries
		:param exchange:
		:param market:
		:param data_type: currently supported are 'history', 'bids', 'asks', 'orders'
		:return:
		"""
		d = self.request('data', exchange_code=exchange, exchange_market=market, type=data_type, json=True)['data']

		res = dict()

		for key in ['history', 'bids', 'asks']:
			if key in list(d.keys()):
				dat = pd.DataFrame.from_records(d[key])

				if 'price' in dat.columns:
					dat.price = dat.price.astype(np.float)

				if 'quantity' in dat.columns:
					dat.quantity = dat.quantity.astype(np.float)

				if 'total' in dat.columns:
					dat.total = dat.total.astype(np.float)

				if 'time_local' in dat.columns:
					dat.time_local = pd.to_datetime(dat.time_local)
					dat.set_index('time_local', inplace=True)

				if 'type' in dat.columns:
					dat.type = dat.type.astype(str)

				if not dat.empty:
					dat['base_ccy'] = d['primary_curr_code']
					dat['counter_ccy'] = d['secondary_curr_code']
					
				res[key] = dat

		return res

	def accounts(self):
		return self.request('accounts')

	def activity(self):
		return self.request('activity')

	def balances(self):
		return self.request('balances')

	def open_orders(self):
		return self.request('orders', json=True)

	def alerts(self):
		all_alerts = self.request('alerts', json=True)['data']
		open_alerts = pd.DataFrame(all_alerts['open_alerts'])
		alert_history = pd.DataFrame(all_alerts['alert_history'])

		return all_alerts # alerts(open_alerts=open_alerts, alert_history=alert_history)

	def exchange_id(self, exchange_code):
		return list(filter(lambda exchange: exchange['exch_code'] == exchange_code, self.exchanges()['data']))[0]['exch_id']

	def exchanges(self):
		return self.request('exchanges')

	def markets(self, exchange_code):
		return self.request('markets', exchange_code=exchange_code)

	def market_id(self, exchange_code, market_name):
		return list(filter(lambda market: market['mkt_name'] == market_name, self.markets(exchange_code)['data']))[0]['mkt_id']

	def history(self, exchange, market):
		return self.data(exchange=exchange, market=market, data_type='history')['history']

	def asks(self, exchange, market):
		return self.data(exchange=exchange, market=market, data_type='asks')['asks']

	def bids(self, exchange, market):
		return self.data(exchange=exchange, market=market, data_type='bids')['bids']

	def orders(self, exchange, market):
		return self.data(exchange=exchange, market=market, data_type='orders')

	def ticker(self, exchange, market):	 
		return self.request('ticker', exchange_code=exchange, exchange_market=market)['data'][0]

	def news_feed(self):
		dat = self.request('newsFeed')
		dat.timestamp = pd.to_datetime(dat.timestamp)

		dat.set_index('timestamp', inplace=True)

		return dat

	def order_types(self):
		dat = self.request('orderTypes', json=True)['data']

		return dict(order_types=pd.DataFrame.from_records(dat['order_types']),
					price_types=pd.DataFrame.from_records(dat['price_types']))

	def refresh_balance(self, auth_id):
		return self.request('refreshBalance', auth_id=auth_id, json=True)

	def add_alert(self, exchange, market, price, note=''):
		return self.request('addAlert',
							exch_code=exchange,
							market_name=market,
							alert_price=price,
							alert_note=note,
							json=True)['notifications']
	def delete_alerts(self):
		for alert in self.alerts()['open_alerts']:
			self.delete_alert(alert['alert_id'])


	def delete_alert(self, alert_id):
		return self.request('deleteAlert', alert_id=alert_id, json=True)['notifications']

	def buy(self, auth_id, exch_id, mkt_id, price_type_id, limit_price, order_quantity, stop_price=''):
		self.add_order(auth_id, exch_id, mkt_id, OrderTypeId.BUY, price_type_id, limit_price, order_quantity, stop_price)

	def sell(self, auth_id, exch_id, mkt_id, price_type_id, limit_price, order_quantity, stop_price=''):
		self.add_order(auth_id, exch_id, mkt_id, OrderTypeId.SELL, price_type_id, limit_price, order_quantity, stop_price)

	def add_order(self, auth_id, exch_id, mkt_id, order_type_id, price_type_id, limit_price, order_quantity, stop_price):
		return self.request('addOrder',
							auth_id = auth_id,
							exch_id=exch_id,
							mkt_id=mkt_id,
							order_type_id=order_type_id,
							price_type_id=price_type_id,
							limit_price=limit_price,
							stop_price=stop_price,
							order_quantity=order_quantity,
							json=True)

	def cancel_order(self, order_id):
		return self.request('cancelOrder', internal_order_id=order_id, json=True)

	def balance_history(self, date):
		"""
		NB: the timestamp columns is the time when the account was last snapshot, not the time the balances were
			effectively refreshed
		:param date:	date str in format YYYY-MM-DD
		:return:		a view of the account balances as of the date provided
		"""
		bh = pd.DataFrame.from_records(self.request('balanceHistory', date=date, json=True)['data']['balance_history'])

		if bh.empty:
			return bh

		acct = self.accounts()[['auth_id', 'exch_name']]

		return pd.merge(bh, acct, on='auth_id', how='left')
