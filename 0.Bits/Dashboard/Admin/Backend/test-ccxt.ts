import ccxt from 'ccxt';
const binance = new ccxt.binance();
console.log('sapiGetConvertTradeFlow' in binance);
console.log('sapiGetAssetTransfer' in binance);
console.log('sapiGetCapitalDepositHisrec' in binance);
console.log('sapiGetCapitalWithdrawHistory' in binance);
