import rateLimit from 'express-rate-limit';

/**
 * Public rate limiter: unauthenticated endpoints (login, health).
 */
export const publicLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT',
      message: 'Too many requests — limit 100 per 15 minutes. Retry later.',
    },
  },
});

/**
 * Authenticated rate limiter: standard admin operations.
 */
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 500,
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT',
      message: 'Too many authenticated requests — limit 500 per 15 minutes.',
    },
  },
});

/**
 * Strict rate limiter: login attempts (brute-force protection).
 */
export const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true,
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT',
      message: 'Too many login attempts. Account temporarily locked.',
    },
  },
});
