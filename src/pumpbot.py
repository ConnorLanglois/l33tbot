from coinigy import Account, Coinigy, PriceTypeId
from telethon import TelegramClient
from telethon.tl.types import UpdateShortMessage, MessageEntityUrl
from telethon.tl.functions.contacts import ResolveUsernameRequest
from time import sleep

import logging
import re

api = ''
secret = ''
endpoint = 'https://api.coinigy.com/api/v1'
uri = 'wss://sc-02.coinigy.com/socketcluster/'
auth_ids = {
	'BTRX': ''
}

api_id = ''
api_hash = ''
phone = ''

users = ('bittrexxnews', 'PumpNotifier')

pc = 50

for key in logging.Logger.manager.loggerDict:
    logging.getLogger(key).setLevel(logging.WARNING)

coin = Coinigy(Account(api, secret, endpoint, uri))
tele = TelegramClient('session', api_id, api_hash, update_workers=1)

user_ids = [list(tele(ResolveUsernameRequest(user)).peer.__dict__.values())[-1] for user in users]

tele.connect()
	
if not tele.is_user_authorized():
	tele.send_code_request(phone)
	tele.sign_in(phone, input('Enter code: '))

def on_update(update):
	if isinstance(update, UpdateShortMessage) and any([update.user_id == user_id for user_id in user_ids]):
		exchange_name = re.search('(?:/.+\.|//){1}(.+).com', update.message).group(1)
		exchange_codes = list(filter(lambda exchange: exchange['exch_name'].lower() == exchange_name.lower(), coin.exchanges()['data']))

		if len(exchange_codes) == 0:
			print('Cannot find exchange code of', exchange)

			return

		exchange_code = exchange_codes[0]['exch_code']

		if exchange_code != 'BTRX':
			print('Exchange not Bittrex')

			return

		length = list(filter(lambda entity: isinstance(entity, MessageEntityUrl), update.entities))[0].length - 44

		market = '/'.join(reversed(re.search(f'MarketName=(.{length})', update.message).group(1).split('-')))

		last_price = float(coin.ticker(exchange_code, market)['last_trade'])
		btc_price = float(coin.ticker('BTRX', 'BTC/USDT')['last_trade'])
		price = last_price * (1 + pc / 100)
		volume = int(5 / btc_price / price)

		print('Buying', volume, 'of', exchange_code, market, 'at', price, 'for', volume * price, '5' + '/' + str(btc_price))
		coin.add_alert(exchange_code, market, price, str(last_price))

tele.add_update_handler(on_update)

while True:
	sleep(5)
