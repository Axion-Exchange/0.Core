import winston from 'winston';
import { config } from '../config/index.js';

const { combine, timestamp, printf, colorize, json } = winston.format;

const devFormat = combine(
  colorize(),
  timestamp({ format: 'HH:mm:ss' }),
  printf(({ timestamp, level, message, source, ...meta }) => {
    const src = source ? `[${source}]` : '';
    const metaStr = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
    return `${timestamp} ${level} ${src} ${message}${metaStr}`;
  }),
);

const prodFormat = combine(
  timestamp(),
  json(),
);

export const logger = winston.createLogger({
  level: config.LOG_LEVEL,
  defaultMeta: { service: '0bits-api' },
  format: config.NODE_ENV === 'production' ? prodFormat : devFormat,
  transports: [
    new winston.transports.Console(),
  ],
});

/**
 * Create a child logger scoped to a specific source module.
 */
export function createLogger(source: string) {
  return logger.child({ source });
}
