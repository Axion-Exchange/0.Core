import { config } from './src/config/index.js';
import { BinanceClient } from './src/lib/binance.js';
import fs from 'fs';

async function test() {
  const apiKey = config.BINANCE_API_KEY;
  const apiSecret = fs.readFileSync(config.BINANCE_API_PRIVATE_KEY_PATH, 'utf8');
  
  const client = new BinanceClient({ apiKey, secret: apiSecret, enableLogging: true });
  
  console.log("Testing with advNo single...");
  try {
    const res2 = await client.request('c2c/ads/updateStatus', 'sapi', 'POST', { advNo: "12877040881292201984", advStatus: 2 });
    console.log("Result2:", res2);
  } catch (e) { console.log("Error2:", e.message || e); }
}

test();
