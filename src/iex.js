const socket = require('socket.io-client');
const rp = require('request-promise-native')

module.exports = class {
	constructor(host, onConnect, onDisconnect, onMessage) {
		this._host = host;

		this._socket = onConnect !== undefined ? socket(this._host) : null;

		if (this._socket !== null) {
			this.onConnect = onConnect;
			this.onDisconnect = onDisconnect;
			this.onMessage = onMessage;
		}
	}

	async tops(...symbols) {
		return this.request('tops', {
			symbols: symbols.join(',')
		});
	}

	async last(...symbols) {
		return this.request('tops/last', {
			symbols: symbols.join(',')
		});
	}

	async hist(date='') {
		return this.request('hist', {
			date: date
		});
	}

	async deep(symbol) {
		return this.request('deep', {
			symbols: symbol
		});
	}

	async book(...symbols) {
		return this.request('deep/book', {
			symbols: symbols.join(',')
		});
	}

	async trades(last = 20, ...symbols) {
		return this.request('deep/trades', {
			symbols: symbols.join(','),
			last: last
		});
	}

	request(path, qs = {}) {
		return rp(this._host + '/' + path, {
			qs: qs
		}).then(data => {
			return data;
		}).catch(error => {
			return error.response.body;
		});
	}

	subscribe(...symbols) {
		this._socket.emit('subscribe', symbols.join(','))
	}

	unsubscribe(...symbols) {
		this._socket.emit('unsubscribe', symbols.join(','))
	}

	set onMessage(onMessage) {
		this._socket.on('message', onMessage)
	}

	set onDisconnect(onDisconnect) {
		this._socket.on('disconnect', onDisconnect)
	}

	set onConnect(onConnect) {
		this._socket.on('connect', onConnect)
	}
}
