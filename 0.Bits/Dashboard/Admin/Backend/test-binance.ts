import ccxt from 'ccxt';
import dotenv from 'dotenv';
dotenv.config();

async function testBinance() {
  const binance = new ccxt.binance({
    apiKey: process.env.BINANCE_API_KEY,
    secret: process.env.BINANCE_API_SECRET,
    enableRateLimit: true,
  });

  try {
    console.log('Testing Binance Connection...');
    const fundingBalances = await binance.sapiPostAssetGetFundingAsset();
    const nonZero = fundingBalances.filter((a: any) => parseFloat(a.free) > 0 || parseFloat(a.locked) > 0);
    console.log('--- Funding Balances ---');
    console.table(nonZero);
  } catch (error) {
    console.error('Failed to fetch from Binance:', error.message);
  }
}

testBinance();
