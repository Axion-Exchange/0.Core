import ccxt from 'ccxt';
const binance = new ccxt.binance();
const methods = Object.keys(binance).filter(k => k.toLowerCase().includes('funding') || k.toLowerCase().includes('c2c'));
console.log(methods);
