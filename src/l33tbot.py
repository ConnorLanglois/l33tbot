from coinigy import Account, Coinigy, PriceTypeId

import logging
import threading
import time

def on_authenticated():
	start_time = None
	block_time = 30
	market_datas = {}
	pc = 3
	order_pc = 1
	working = False

	def on_trade(trade):
		nonlocal working

		if not working:
			print('Working')

			working = True

		# print('TRADE', trade.exchange, trade.label, '(' + trade.time_local + '):', '{:<4}'.format(trade.type), *['{:.10f}'.format(data) for data in (trade.price, trade.quantity, trade.total)])

		market_datas[trade.label]['acc_price'] += trade.price
		market_datas[trade.label]['n_trades'] += 1

	def on_tick():
		nonlocal start_time, market_datas

		while True:
			time.sleep(block_time - (time.time() - start_time))
			start_time = time.time()

			for market_data in market_datas:
				last_price = market_datas[market_data]['last_price']
				price = market_datas[market_data]['price']
				acc_price = market_datas[market_data]['acc_price']
				n_trades = market_datas[market_data]['n_trades']
				exchange_code = market_datas[market_data]['exch_code']

				price = last_price if n_trades == 0 else acc_price / n_trades

				# print('\tBlock ended', 'BTRX', market_data, last_price, price, acc_price, n_trades)

				if last_price is not None:
					if price > (1 + pc / 100) * last_price or last_price > (1 + pc / 100) * price:
						price_pc = (price - last_price) / last_price * 100
						btc_price = float(coin.ticker('BTRX', 'BTC/USDT')['last_trade'])
						cur_price = float(coin.ticker(exchange_code, market_data)['last_trade'])
						order_price = cur_price * (1 + (order_pc * (1 if price > last_price else -1) / 100))
						volume = int(5 / btc_price / price)

						print(
							'\t\t(' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time - block_time)),
							'-',
							time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)) + ')',
							'\t' + ('PUMP' if price > last_price else 'DUMP'),
							exchange_code,
							'{:<9}'.format(market_data),
							'{:<10}'.format('(' + ('+' if price > last_price else '-') + ('Infinity' if last_price == 0 else '{:.2f}'.format(abs(price_pc))) + '%):'),
							'{:.8f}'.format(last_price),
							'-',
							'{:.8f}'.format(price)
						)

						print('\t\t\t', 'Buying' if price > last_price else 'Selling', volume, 'of', exchange_code, market_data, '@', order_price, 'for', volume * order_price, '5' + '/' + str(btc_price))
						coin.add_alert(exchange_code, market_data, order_price, str(last_price))

				market_datas[market_data]['last_price'] = price
				market_datas[market_data]['price'] = 0
				market_datas[market_data]['acc_price'] = 0
				market_datas[market_data]['n_trades'] = 0

				# print('\tBlock started', 'BTRX', market_data)

	for market in coin.markets('BTRX')['data']:
		market_datas[market['mkt_name']] = {
			'exch_code': market['exch_code'],
			'last_price': None,
			'price': 0,
			'acc_price': 0,
			'n_trades': 0
		}

		coin.subscribe_trades('BTRX', market['mkt_name'], on_trade)

	# print('\tBlocks started')

	start_time = time.time()

	threading.Thread(target=on_tick).start()

api = ''
secret = ''
endpoint = 'https://api.coinigy.com/api/v1'
uri = 'wss://sc-02.coinigy.com/socketcluster/'
auth_ids = {
	'BTRX': ''
}

logging.getLogger().disabled = True
logging.getLogger('urllib3').setLevel(logging.WARNING)

coin = Coinigy(Account(api, secret, endpoint, uri))

coin.connect(on_authenticated)
