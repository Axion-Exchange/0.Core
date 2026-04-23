import { mexcSpotWorker } from './src/workers/mexc-spot.worker.js';
await mexcSpotWorker.run();
console.log('Done!');
