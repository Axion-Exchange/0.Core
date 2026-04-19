import cors from 'cors';
import { config } from '../config/index.js';

/**
 * Centralized CORS configuration.
 * Reads allowed origins from CORS_ORIGINS env var (comma-separated).
 */
export function createCorsMiddleware() {
  const allowedOrigins = config.CORS_ORIGINS
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean);

  return cors({
    origin: (origin, callback) => {
      // Allow requests with no origin (server-to-server, curl, etc.)
      if (!origin) {
        callback(null, true);
        return;
      }

      if (allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error(`Origin ${origin} not permitted by CORS policy`));
      }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Correlation-ID'],
    exposedHeaders: ['X-Correlation-ID', 'X-RateLimit-Remaining'],
    maxAge: 86400, // 24h preflight cache
  });
}
