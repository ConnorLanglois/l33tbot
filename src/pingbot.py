from coinigy import Account, Coinigy, PriceTypeId
from telethon import TelegramClient
from telethon.tl.types import UpdateShortMessage, MessageEntityTextUrl
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

for key in logging.Logger.manager.loggerDict:
    logging.getLogger(key).setLevel(logging.WARNING)

coin = Coinigy(Account(api, secret, endpoint, uri))
tele = TelegramClient('session', api_id, api_hash, update_workers=1)

tele.connect()
	
if not tele.is_user_authorized():
	tele.send_code_request(phone)
	tele.sign_in(phone, input('Enter code: '))

def on_update(update):
	if isinstance(update, UpdateShortMessage) and update.user_id == tele(ResolveUsernameRequest('CryptoPingGolfBot')).peer.user_id and 'BTC' in update.message:
		exchange_name = re.search('on (.+)\n', update.message).group(1)
		exchange_codes = list(filter(lambda exchange: exchange['exch_name'] == exchange_name, coin.exchanges()['data']))

		if len(exchange_codes) == 0:
			print('Cannot find exchange code of', exchange)

			return

		exchange_code = exchange_codes[0]['exch_code']
		market = re.search('#(.+)\n', update.message).group(1) + '/BTC'
		price_pc = float(re.search('BTC\n(.+)%', update.message).group(1))

		last_price = float(coin.ticker(exchange_code, market)['last_trade'])
		btc_price = float(coin.ticker('BTRX', 'BTC/USDT')['last_trade'])
		price = last_price * (1 + price_pc / 3 / 100)
		volume = int(5 / btc_price / price)

		print('Buying', volume, 'of', exchange_code, market, 'at', price, 'for', volume * price, '5' + '/' + str(btc_price))
		coin.add_alert(exchange_code, market, price, str(last_price))

tele.add_update_handler(on_update)

while True:
	sleep(5)
