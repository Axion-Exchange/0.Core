import { Router } from 'express';
import { authService } from '../services/auth.service.js';
import { validateBody } from '../middleware/validate.js';
import { requireAuth, requireRole } from '../middleware/auth.js';
import { loginLimiter } from '../middleware/rate-limit.js';
import { loginSchema, changePasswordSchema, registerAdminSchema } from '../validators/auth.schema.js';
import { sendSuccess } from '../lib/response.js';

const router = Router();

// POST /login — Authenticate admin
router.post('/login', loginLimiter, validateBody(loginSchema), async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const ip = req.ip ?? req.socket.remoteAddress ?? 'unknown';
    const userAgent = req.headers['user-agent'];
    const result = await authService.login(email, password, ip, userAgent);
    sendSuccess(res, result);
  } catch (err) { next(err); }
});

// POST /logout — Revoke session + blacklist JWT in Redis
router.post('/logout', requireAuth, async (req, res, next) => {
  try {
    if (req.admin?.sessionId) {
      const jti = (req.admin as any).jti || req.admin.sessionId;
      const exp = (req.admin as any).exp;
      await authService.logout(req.admin.sessionId, jti, exp);
    }
    sendSuccess(res, { message: 'Logged out successfully' });
  } catch (err) { next(err); }
});

// GET /me — Current admin profile
router.get('/me', requireAuth, async (req, res, next) => {
  try {
    const profile = await authService.getProfile(req.admin!.sub);
    sendSuccess(res, profile);
  } catch (err) { next(err); }
});

// PUT /me/password — Change password
router.put('/me/password', requireAuth, validateBody(changePasswordSchema), async (req, res, next) => {
  try {
    const { currentPassword, newPassword } = req.body;
    await authService.changePassword(req.admin!.sub, currentPassword, newPassword);
    sendSuccess(res, { message: 'Password changed. All sessions revoked.' });
  } catch (err) { next(err); }
});

// POST /register — Create new admin (SUPER_ADMIN only)
router.post('/register', requireAuth, requireRole('SUPER_ADMIN'), validateBody(registerAdminSchema), async (req, res, next) => {
  try {
    const admin = await authService.createAdmin(req.body);
    sendSuccess(res, admin, 201);
  } catch (err) { next(err); }
});

export { router as authRouter };
