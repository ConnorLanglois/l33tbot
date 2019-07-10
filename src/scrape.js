var element = document.querySelectorAll('[name=batch]')[0];
var functions = {};
var prevFunction = undefined;

var out = '';

while (element = element.nextElementSibling) {
	if (element.tagName === 'H2' && element.className === 'beta') {
		let key = '';
		let nextElement = element;

		while ((nextElement = nextElement.nextElementSibling) && (nextElement.tagName !== 'H2' && nextElement.tagName !== 'beta')) {
			if (nextElement.tagName === 'UL') {
				let match = nextElement.firstElementChild.innerText.split('').reverse().join('').match(/\?([^\/]+)/);

				if (match === null) {
					match = nextElement.firstElementChild.innerText.split('').reverse().join('').match(/([^\/]+)/)
				}

				key = match[1].split('').reverse().join('');

				break;
			}
		}

		key = key.split('-').map((word, i) => {
			if (i !== 0) {
				word = word.charAt(0).toUpperCase() + word.substring(1);
			}

			return word;
		}).join('');

		console.log(key);

		functions[key] = {
			params: []
		};
		prevFunction = functions[key];
		prevKey = key;
	}

	if (element.tagName === 'TABLE') {
		const th = element.children[0];

		if (th.innerText.includes('Option') || th.innerText.includes('Parameter')) {
			let trs = element.children[1].children;

			for (let tr of trs) {
				let param = tr.children[0].innerText;

				prevFunction.params.push(param === 'symbols' ? '...symbols' : param);
			}

			if (i = prevFunction.params.indexOf('...symbols')) {
				prevFunction.params.push(prevFunction.params.splice(i, 1)[0]);
			}
		} else if (th.innerText.includes('Range')) {
			prevFunction.params.push('range');
		}
	}
}

for (let func in functions) {
	let params = functions[func].params;
	
	out += `async ${func}(${params.join(', ')}) {\n\treturn this.request('${func}'${params.length > 0 ? `, {\n\t\t${params.map(param => param === '...symbols' ? "symbols: symbols.join(',')" : `${param}: ${param}`).join(',\n\t\t')}\n\t}` : ''});\n}\n\n`;
}
