const ccxt = require('ccxt');
const fs = require('fs');

async function run() {
  require('dotenv').config();
  const apiKey = process.env.BINANCE_API_KEY;
  let secret = process.env.BINANCE_API_SECRET;
  if (!secret) {
    secret = fs.readFileSync(process.env.BINANCE_API_PRIVATE_KEY_PATH, 'utf8');
  }
  
  const exchange = new ccxt.binance({ apiKey, secret });
  
  console.log("Testing updateStatus with advNo");
  try {
    const res = await exchange.request('c2c/ads/updateStatus', 'sapi', 'POST', { advNo: "12877040881292201984", advStatus: 2 });
    console.log(res);
  } catch (e) {
    console.log(e.message);
  }
}
run();
