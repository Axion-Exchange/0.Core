import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { errorHandler } from './middleware/error';

const app = express();

// 1. Extreme Transport Security
app.use(helmet({
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  frameguard: { action: 'deny' }
}));

// 2. Strict CORS policy
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://0.bits.axion.exchange'] // Strict institutional whitelisting
    : 'http://localhost:3000',
  credentials: true
}));

// 3. Payload parsing & limiting to prevent buffer overflow attacks
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

// 4. Rate braking to mitigate brute-forcing
const institutionalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per `window`
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Strict rate limit exceeded. Institutional lockdown initiated.' }
});

app.use('/api', institutionalLimiter);

// --- 5. Phase 4: API Endpoint Scaffolding (Stubs) ---
import { Router } from 'express';
const complianceRouter = Router();
complianceRouter.get('/users', (req, res) => res.json({ msg: 'Compliance Users Mock' }));

const treasuryRouter = Router();
treasuryRouter.get('/aggregate', (req, res) => res.json({ msg: 'Treasury NAV Mock' }));

const p2pRouter = Router();
p2pRouter.get('/orders/active', (req, res) => res.json({ msg: 'Active P2P Orders Mock' }));

const infraRouter = Router();
infraRouter.get('/health', (req, res) => res.json({ status: 'SECURE_AND_OPERATIONAL' }));

app.use('/api/v1/compliance', complianceRouter);
app.use('/api/v1/treasury', treasuryRouter);
app.use('/api/v1/p2p', p2pRouter);
app.use('/api/v1/infrastructure', infraRouter);

// Global Error Interceptor
app.use(errorHandler);

const PORT = process.env.PORT || 4000;

app.listen(PORT, () => {
  console.log(`[INSTITUTIONAL CORE] Secure API enforcing on port ${PORT}`);
});
