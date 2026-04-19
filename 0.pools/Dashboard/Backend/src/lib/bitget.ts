import fs from 'fs';
import path from 'path';

interface BitgetTicker {
  symbol: string;
  lastPr: string;
  baseVolume: string; // 24h volume in base asset
  quoteVolume: string; // 24h volume in quote asset
}

const CACHE_CSV = path.join(process.cwd(), 'bitget_data.csv');
const CACHE_DURATION_MS = 6 * 60 * 60 * 1000; // 6 Hours

// Helper to reliably read the last line of the CSV
function readLatestFromCSV(): { timestamp: number; data: any } | null {
  if (!fs.existsSync(CACHE_CSV)) return null;
  
  try {
    const content = fs.readFileSync(CACHE_CSV, 'utf-8').trim();
    if (!content) return null;
    
    const lines = content.split('\n');
    const lastLine = lines[lines.length - 1];
    
    const [ts_str, vol_str, chart_json] = lastLine.split('|'); // Using pipe to avoid conflicting with JSON commas
    if (!ts_str || !vol_str || !chart_json) return null;
    
    return {
      timestamp: parseInt(ts_str, 10),
      data: {
        totalVolume24h: parseFloat(vol_str),
        chart30D: JSON.parse(chart_json),
      }
    };
  } catch (e) {
    console.error('[BITGET] Failed to read CSV cache', e);
    return null;
  }
}

function appendToCSV(timestamp: number, metrics: any) {
  try {
    const row = `${timestamp}|${metrics.totalVolume24h}|${JSON.stringify(metrics.chart30D)}\n`;
    fs.appendFileSync(CACHE_CSV, row);
  } catch (e) {
    console.error('[BITGET] Failed to append to CSV', e);
  }
}

export async function fetchGlobalMarketMetrics() {
  const now = Date.now();

  const latest = readLatestFromCSV();
  if (latest && (now - latest.timestamp < CACHE_DURATION_MS)) {
     return latest.data;
  }

  try {
    const response = await fetch('https://api.bitget.com/api/v2/spot/market/tickers');
    const res: any = await response.json();
    
    if (res && res.code === '00000' && Array.isArray(res.data)) {
      const tickers: BitgetTicker[] = res.data;
      
      let totalVolume = 0;
      
      // Calculate global volume against stablecoins (proxy for fiat)
      tickers.forEach(t => {
        if (t.symbol.endsWith('USDT') || t.symbol.endsWith('USDC') || t.symbol.endsWith('EUR')) {
           totalVolume += Number(t.quoteVolume);
        }
      });

      // User constraint: Values should ONLY be 0.1% of the values Bitget has
      totalVolume = totalVolume * 0.001;

      // Ensure stable synthetic volume trend
      const chartPoints = Array.from({ length: 12 }).map((_, i) => {
         const baseline = (totalVolume / 30);
         return Math.floor(baseline * (0.8 + Math.random() * 0.3));
      });

      const metrics = {
        totalVolume24h: totalVolume,
        chart30D: chartPoints
      };
      
      // Save successfully fetched data to CSV
      appendToCSV(now, metrics);

      return metrics;
    }
    throw new Error('Invalid Bitget Response');
  } catch (err) {
    console.error('[BITGET] Failed to fetch. Using CSV strictly:', err);
    if (latest) {
      return latest.data; // Enforce CSV display even if API is completely down
    }
    
    return {
      totalVolume24h: 0,
      chart30D: []
    };
  }
}
