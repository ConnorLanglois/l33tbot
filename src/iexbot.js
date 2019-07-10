const https = require('https');
const Iex = require('./iex');

const host = 'https://ws-api.iextrading.com/1.0';
const endpoint = 'tops';

const markets = {}

const iex = new Iex(`${host}`);

(async () => {
	console.log(JSON.parse(await iex.trades(20, 'aapl')));
})();

/*
https.get({
	host: 'ws-api.iextrading.com',
	path: '/1.0/tops'
}, res => {
	let data = '';

	res.on('data', chunk => {
		data += chunk;
	})

	res.on('end', () => {
		const symbols = JSON.parse(data).map(market => market.symbol);
		
		symbols.reduce((markets, symbol) => Object.assign(markets, {
			[symbol]: {
				lastPrice: undefined,
				accPrice: 0,
				nTrades: 0,
				lastSaleTime: 0
			}
		}), markets);

		const iex = new Iex(`${host}/${endpoint}`, () => {
			console.log('Connected');
			iex.subscribe(symbols);

			setInterval(() => {
				for (const market in markets) {
					const lastPrice = markets[market].lastPrice;
					const accPrice = markets[market].accPrice;
					const nTrades = markets[market].nTrades;
					const price = nTrades === 0 ? lastPrice : accPrice / nTrades;

					if (lastPrice !== undefined && (price > 1.03 * lastPrice || lastPrice > 1.03 * price)) {
						console.log(
							'(' + new Date().toISOString() + ')',
							'\t' + price > lastPrice ? 'PUMP' : 'DUMP',
							market,
							'(' + (price > lastPrice ? '+' : '-') + Math.round(Math.abs((price - lastPrice) / lastPrice * 100) * 100) / 100 + '%):',
							nTrades,
							'',
							lastPrice,
							'-',
							price
						);
					}

					markets[market].lastPrice = price;
					markets[market].accPrice = 0;
					markets[market].nTrades = 0;
				}
			}, 30000);
		}, () => {
			console.log('Disconnected');
		}, tradeRaw => {
			trade = JSON.parse(tradeRaw);
			market = markets[trade.symbol];

			if (trade.time !== market.lastSaleTime) {
				market.accPrice += trade.price;
				market.nTrades++;
				market.lastSaleTime = trade.time;
			}
		})
	});
});
*/