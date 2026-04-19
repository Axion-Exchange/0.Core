import { Router, Request, Response } from 'express';
import { z } from 'zod';
import prisma from '../lib/prisma';
import { hashPassword, comparePassword, signToken, generateCSRFToken } from '../lib/auth';
import { authenticate, validateSession, requireReauth } from '../middleware/auth';
import { sendPasswordResetOTP } from '../lib/email';
import crypto from 'crypto';

const router = Router();

// ─── SCHEMAS ────────────────────────────────────────────

const signupSchema = z.object({
  name: z.string().min(2).max(100),
  email: z.string().email(),
  password: z.string().min(8).max(128),
  passwordConfirmation: z.string(),
}).refine((data) => data.password === data.passwordConfirmation, {
  message: "Passwords don't match",
  path: ['passwordConfirmation'],
});

const signinSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

// ─── POST /api/auth/signup ──────────────────────────────

router.post('/signup', async (req: Request, res: Response) => {
  try {
    const parsed = signupSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, message: parsed.error.errors[0].message });
      return;
    }

    const { name, password } = parsed.data;
    const email = parsed.data.email.toLowerCase();

    // Server-side reCAPTCHA verification
    const recaptchaToken = req.headers['x-recaptcha-token'] as string;
    const recaptchaSecret = process.env.RECAPTCHA_SECRET_KEY;
    if (recaptchaSecret) {
      if (!recaptchaToken) {
        res.status(400).json({ success: false, message: 'reCAPTCHA verification required.' });
        return;
      }
      try {
        const verifyRes = await fetch('https://www.google.com/recaptcha/api/siteverify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: `secret=${recaptchaSecret}&response=${recaptchaToken}`,
        });
        const verifyData = await verifyRes.json() as { success: boolean };
        if (!verifyData.success) {
          res.status(400).json({ success: false, message: 'reCAPTCHA verification failed.' });
          return;
        }
      } catch {
        console.error('[AUTH] reCAPTCHA verification request failed');
        // Allow signup if reCAPTCHA service is down — don't block users
      }
    }

    // Check if user exists
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      res.status(409).json({ success: false, message: 'An account with this email already exists' });
      return;
    }

    // Get default client role
    let clientRole = await prisma.userRole.findUnique({ where: { slug: 'client' } });
    if (!clientRole) {
      clientRole = await prisma.userRole.create({
        data: { slug: 'client', name: 'Client', isDefault: true },
      });
    }

    const passwordHash = await hashPassword(password);

    const user = await prisma.user.create({
      data: {
        email,
        passwordHash,
        name,
        roleId: clientRole.id,
        status: 'ACTIVE', // In production, set to INACTIVE and require email verification
      },
    });

    // Log the event
    await prisma.systemLog.create({
      data: {
        event: 'USER_SIGNUP',
        userId: user.id,
        description: `New user registered: ${email}`,
        ipAddress: req.ip || 'unknown',
      },
    });

    // Create server-side session
    const session = await prisma.session.create({
      data: {
        sessionToken: crypto.randomBytes(32).toString('hex'),
        userId: user.id,
        expires: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24h
        ipAddress: req.ip || 'unknown',
        userAgent: req.headers['user-agent'] || 'unknown',
      },
    });

    const token = signToken({
      userId: user.id,
      email: user.email,
      roleSlug: clientRole.slug,
      sessionId: session.id,
    });

    // Set httpOnly cookie — cross-origin safe
    res.cookie('__session', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'none', // Required for cross-origin (Cloudflare → EC2)
      maxAge: 24 * 60 * 60 * 1000, // 24h
      path: '/',
    });

    res.status(201).json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          status: user.status,
        },
        token,
      },
    });
  } catch (error) {
    console.error('[AUTH] Signup error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/auth/signin ──────────────────────────────

router.post('/signin', async (req: Request, res: Response) => {
  try {
    const parsed = signinSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, message: 'Invalid email or password' });
      return;
    }

    const { password } = parsed.data;
    const email = parsed.data.email.toLowerCase();

    const user = await prisma.user.findUnique({
      where: { email },
      include: { role: true },
    });

    // Timing attack prevention: simulate bcrypt delay if user doesn't exist
    if (!user) {
      await new Promise(r => setTimeout(r, 600 + Math.random() * 400));
      res.status(401).json({ success: false, message: 'Invalid email or password' });
      return;
    }

    // Server-side lockout check
    if (user.lockedUntil && user.lockedUntil > new Date()) {
      await new Promise(r => setTimeout(r, 600 + Math.random() * 400));
      res.status(403).json({ 
        success: false, 
        message: 'Account temporarily locked due to multiple failed login attempts.' 
      });
      return;
    }

    if (user.status === 'BLOCKED') {
      res.status(403).json({ success: false, message: 'Account has been suspended' });
      return;
    }

    const valid = await comparePassword(password, user.passwordHash);
    
    if (!valid) {
      const newAttempts = user.failedLoginAttempts + 1;
      const isLocked = newAttempts >= 5;
      const lockedUntil = isLocked ? new Date(Date.now() + 15 * 60 * 1000) : null;
      
      await prisma.user.update({
        where: { id: user.id },
        data: { failedLoginAttempts: newAttempts, lockedUntil },
      });

      if (isLocked) {
        await prisma.systemLog.create({
          data: {
            event: 'ACCOUNT_LOCKED',
            userId: user.id,
            description: `Account temporarily locked due to 5 consecutive failed login attempts`,
            ipAddress: req.ip || 'unknown',
          },
        });
      }

      const msg = isLocked 
        ? 'Account temporarily locked due to multiple failed login attempts.'
        : 'Invalid email or password';
        
      res.status(401).json({ success: false, message: msg });
      return;
    }

    // Success: Update last sign in and explicitly reset lockout tracking
    await prisma.user.update({
      where: { id: user.id },
      data: { 
        lastSignInAt: new Date(), 
        failedLoginAttempts: 0, 
        lockedUntil: null 
      },
    });

    // Log the event
    await prisma.systemLog.create({
      data: {
        event: 'USER_SIGNIN',
        userId: user.id,
        description: `User signed in: ${email}`,
        ipAddress: req.ip || 'unknown',
      },
    });

    // Create server-side session
    const session = await prisma.session.create({
      data: {
        sessionToken: crypto.randomBytes(32).toString('hex'),
        userId: user.id,
        expires: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24h
        ipAddress: req.ip || 'unknown',
        userAgent: req.headers['user-agent'] || 'unknown',
      },
    });

    const token = signToken({
      userId: user.id,
      email: user.email,
      roleSlug: user.role.slug,
      sessionId: session.id,
    });

    res.cookie('__session', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'none',
      maxAge: 24 * 60 * 60 * 1000,
      path: '/',
    });

    res.json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          status: user.status,
          role: user.role.slug,
        },
        // Token included for backward compat — will be removed after full migration
        token,
      },
    });
  } catch (error) {
    console.error('[AUTH] Signin error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /api/auth/me ───────────────────────────────────

router.get('/me', authenticate, async (req: Request, res: Response) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user!.userId },
      include: { role: true },
    });

    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    res.json({
      success: true,
      data: {
        id: user.id,
        email: user.email,
        name: user.name,
        status: user.status,
        avatar: user.avatar,
        role: user.role.slug,
        country: user.country,
        timezone: user.timezone,
        createdAt: user.createdAt,
      },
    });
  } catch (error) {
    console.error('[AUTH] Me error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/auth/signout ─────────────────────────────

router.post('/signout', authenticate, async (req: Request, res: Response) => {
  try {
    // Delete server-side session
    if (req.user?.sessionId) {
      await prisma.session.deleteMany({ where: { id: req.user.sessionId } });
    }

    // Log the event
    await prisma.systemLog.create({
      data: {
        event: 'USER_SIGNOUT',
        userId: req.user?.userId || 'unknown',
        description: `User signed out`,
        ipAddress: req.ip || 'unknown',
      },
    });

    // Clear all auth cookies
    res.clearCookie('__session', { httpOnly: true, secure: true, sameSite: 'none', path: '/' });
    res.clearCookie('__reauth', { httpOnly: true, secure: true, sameSite: 'none', path: '/' });

    res.json({ success: true, message: 'Signed out successfully' });
  } catch (error) {
    // Still clear cookies even if DB cleanup fails
    res.clearCookie('__session', { httpOnly: true, secure: true, sameSite: 'none', path: '/' });
    res.json({ success: true, message: 'Signed out' });
  }
});

// ─── GET /api/auth/csrf-token ───────────────────────────
// Returns a CSRF token tied to the current session

router.get('/csrf-token', authenticate, (req: Request, res: Response) => {
  if (!req.user?.sessionId) {
    res.status(401).json({ success: false, message: 'No session' });
    return;
  }
  const csrfToken = generateCSRFToken(req.user.sessionId);
  res.json({ success: true, data: { csrfToken } });
});

// ─── POST /api/auth/reauth ──────────────────────────────
// Re-authenticate with password for sensitive operations

router.post('/reauth', authenticate, async (req: Request, res: Response) => {
  try {
    const { password } = req.body;
    if (!password) {
      res.status(400).json({ success: false, message: 'Password is required' });
      return;
    }

    const user = await prisma.user.findUnique({ where: { id: req.user!.userId } });
    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    const valid = await comparePassword(password, user.passwordHash);
    if (!valid) {
      res.status(401).json({ success: false, message: 'Incorrect password' });
      return;
    }

    // Issue a short-lived reauth token (5 minutes)
    const reauthToken = signToken({
      userId: user.id,
      email: user.email,
      roleSlug: req.user!.roleSlug,
      sessionId: req.user!.sessionId,
    });

    res.cookie('__reauth', reauthToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'none',
      maxAge: 5 * 60 * 1000, // 5 minutes
      path: '/',
    });

    res.json({ success: true, message: 'Re-authentication successful' });
  } catch (error) {
    console.error('[AUTH] Reauth error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/auth/reset-password ──────────────────────
// Stage 1: Send 6-digit OTP to user's email

router.post('/reset-password', async (req: Request, res: Response) => {
  try {
    const email = req.body.email?.toLowerCase();
    if (!email) {
      res.status(400).json({ success: false, message: 'Email is required' });
      return;
    }

    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) {
      // Don't reveal if email exists — always return success
      res.json({ success: true, message: 'If that email exists, a reset code has been sent.' });
      return;
    }

    // Generate 6-digit OTP
    const crypto = require('crypto');
    const code = crypto.randomInt(100000, 999999).toString();
    const token = crypto.randomBytes(32).toString('hex');
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000); // 15 minutes

    // Invalidate any existing tokens
    await prisma.passwordResetToken.updateMany({
      where: { userId: user.id, usedAt: null },
      data: { usedAt: new Date() },
    });

    await prisma.passwordResetToken.create({
      data: { userId: user.id, code, token, expiresAt },
    });

    // Send OTP email (falls back to console.log in dev mode)
    await sendPasswordResetOTP(email, code);

    res.json({
      success: true,
      message: 'A 6-digit verification code has been sent to your email.',
      ...(process.env.NODE_ENV !== 'production' && { _devCode: code }),
    });
  } catch (error) {
    console.error('[AUTH] Reset password error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/auth/reset-password-verify ───────────────
// Validate a reset token before showing the password form

router.post('/reset-password-verify', async (req: Request, res: Response) => {
  try {
    const { token } = req.body;
    if (!token) {
      res.status(400).json({ success: false, message: 'Token is required' });
      return;
    }

    const resetToken = await prisma.passwordResetToken.findUnique({
      where: { token },
    });

    if (!resetToken || resetToken.usedAt || resetToken.expiresAt < new Date()) {
      res.status(400).json({ success: false, message: 'Invalid or expired reset token.' });
      return;
    }

    res.json({ success: true, message: 'Token is valid.' });
  } catch (error) {
    console.error('[AUTH] Reset token verify error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/auth/change-password ─────────────────────
// Accepts EITHER { token, newPassword } OR { email, code, newPassword }

router.post('/change-password', async (req: Request, res: Response) => {
  try {
    const { token, code, newPassword } = req.body;
    const email = req.body.email?.toLowerCase();

    if (!newPassword || newPassword.length < 8) {
      res.status(400).json({ success: false, message: 'Password must be at least 8 characters.' });
      return;
    }

    let userId: string | null = null;

    if (token) {
      // URL-based reset (from change-password page)
      const resetToken = await prisma.passwordResetToken.findUnique({ where: { token } });
      if (!resetToken || resetToken.usedAt || resetToken.expiresAt < new Date()) {
        res.status(400).json({ success: false, message: 'Invalid or expired reset token.' });
        return;
      }
      userId = resetToken.userId;
      await prisma.passwordResetToken.update({ where: { id: resetToken.id }, data: { usedAt: new Date() } });
    } else if (email && code) {
      // OTP-based reset (from reset-password page stage 2)
      const user = await prisma.user.findUnique({ where: { email } });
      if (!user) {
        res.status(400).json({ success: false, message: 'Invalid email or code.' });
        return;
      }
      const resetToken = await prisma.passwordResetToken.findFirst({
        where: { userId: user.id, code, usedAt: null, expiresAt: { gt: new Date() } },
        orderBy: { createdAt: 'desc' },
      });
      if (!resetToken) {
        res.status(400).json({ success: false, message: 'Invalid or expired verification code.' });
        return;
      }
      userId = user.id;
      await prisma.passwordResetToken.update({ where: { id: resetToken.id }, data: { usedAt: new Date() } });
    } else {
      res.status(400).json({ success: false, message: 'Provide either {token, newPassword} or {email, code, newPassword}.' });
      return;
    }

    const passwordHash = await hashPassword(newPassword);
    await prisma.user.update({ where: { id: userId }, data: { passwordHash } });

    res.json({ success: true, message: 'Password updated successfully.' });
  } catch (error) {
    console.error('[AUTH] Change password error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/auth/verify-email ────────────────────────

router.post('/verify-email', async (req: Request, res: Response) => {
  try {
    const { token } = req.body;
    if (!token) {
      res.status(400).json({ success: false, message: 'Token is required' });
      return;
    }

    // Verify the JWT
    const { verifyToken } = require('../lib/auth');
    let payload: any;
    try {
      payload = verifyToken(token);
    } catch {
      res.status(400).json({ success: false, message: 'Invalid or expired verification token.' });
      return;
    }

    if (!payload?.userId || payload?.purpose !== 'email-verify') {
      res.status(400).json({ success: false, message: 'Invalid verification token.' });
      return;
    }

    const user = await prisma.user.findUnique({ where: { id: payload.userId } });
    if (!user) {
      res.status(404).json({ success: false, message: 'User not found.' });
      return;
    }

    if (user.emailVerifiedAt) {
      res.json({ success: true, message: 'Email already verified.' });
      return;
    }

    await prisma.user.update({
      where: { id: user.id },
      data: { emailVerifiedAt: new Date(), status: 'ACTIVE' },
    });

    res.json({ success: true, message: 'Email verified successfully.' });
  } catch (error) {
    console.error('[AUTH] Verify email error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /api/v1/auth/2fa/setup ─────────────────────────
// Generate TOTP secret + QR code for authenticator app setup

router.get('/2fa/setup', authenticate, async (req: Request, res: Response) => {
  try {
    const crypto = require('crypto');
    // Generate a random 20-byte secret encoded in base32
    const secret = crypto.randomBytes(20).toString('hex').slice(0, 20).toUpperCase();

    const user = await prisma.user.findUnique({ where: { id: req.user!.userId } });
    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    // Store secret temporarily (not yet enabled until verified)
    await prisma.user.update({
      where: { id: user.id },
      data: { twoFactorSecret: secret },
    });

    // Build otpauth URI for QR code
    const issuer = '0pools';
    const otpauthUrl = `otpauth://totp/${encodeURIComponent(issuer)}:${encodeURIComponent(user.email)}?secret=${secret}&issuer=${encodeURIComponent(issuer)}&digits=6&period=30`;

    // Generate QR code as data URL
    // Note: In production, use the 'qrcode' package. For now, return the URL for client-side QR generation.
    let qrCode = otpauthUrl;
    try {
      const QRCode = require('qrcode');
      qrCode = await QRCode.toDataURL(otpauthUrl);
    } catch {
      // qrcode package not installed — return otpauth URL as fallback
    }

    res.json({
      success: true,
      data: { qrCode, secret, otpauthUrl },
    });
  } catch (error) {
    console.error('[AUTH] 2FA setup error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/v1/auth/verify-2fa ───────────────────────
// Verify a 6-digit TOTP code (used during login + enable flow)

router.post('/verify-2fa', authenticate, async (req: Request, res: Response) => {
  try {
    const { code } = req.body;
    if (!code || code.length !== 6) {
      res.status(400).json({ success: false, message: 'Please provide a 6-digit code.' });
      return;
    }

    const user = await prisma.user.findUnique({
      where: { id: req.user!.userId },
      include: { role: true },
    });

    if (!user || !user.twoFactorSecret) {
      res.status(400).json({ success: false, message: '2FA is not set up for this account.' });
      return;
    }

    // TOTP verification: check if code matches secret with ±1 time step tolerance
    const crypto = require('crypto');
    const timeStep = Math.floor(Date.now() / 30000);
    let isValid = false;

    for (let i = -1; i <= 1; i++) {
      const time = timeStep + i;
      const timeBuffer = Buffer.alloc(8);
      timeBuffer.writeBigInt64BE(BigInt(time));
      const hmac = crypto.createHmac('sha1', Buffer.from(user.twoFactorSecret, 'ascii'));
      hmac.update(timeBuffer);
      const hash = hmac.digest();
      const offset = hash[hash.length - 1] & 0xf;
      const otp = ((hash.readUInt32BE(offset) & 0x7fffffff) % 1000000).toString().padStart(6, '0');
      if (otp === code) {
        isValid = true;
        break;
      }
    }

    if (!isValid) {
      res.status(400).json({ success: false, message: 'Invalid verification code. Please try again.' });
      return;
    }

    // Enable 2FA if not already enabled
    if (!user.twoFactorEnabled) {
      await prisma.user.update({
        where: { id: user.id },
        data: { twoFactorEnabled: true },
      });
    }

    // Issue a fresh token (upgraded — no longer requires 2FA)
    // Create a new session for the 2FA-verified state
    const session = await prisma.session.create({
      data: {
        sessionToken: crypto.randomBytes(32).toString('hex'),
        userId: user.id,
        expires: new Date(Date.now() + 24 * 60 * 60 * 1000),
        ipAddress: req.ip || 'unknown',
        userAgent: req.headers['user-agent'] || 'unknown',
      },
    });

    const accessToken = signToken({
      userId: user.id,
      email: user.email,
      roleSlug: user.role.slug,
      sessionId: session.id,
    });

    // Set upgraded cookie
    res.cookie('__session', accessToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'none',
      maxAge: 24 * 60 * 60 * 1000,
      path: '/',
    });

    res.json({
      success: true,
      message: '2FA verified successfully.',
      data: { accessToken },
    });
  } catch (error) {
    console.error('[AUTH] 2FA verify error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /api/v1/auth/disable-2fa ──────────────────────

router.post('/disable-2fa', authenticate, async (req: Request, res: Response) => {
  try {
    const { password } = req.body;
    if (!password) {
      res.status(400).json({ success: false, message: 'Password is required to disable 2FA.' });
      return;
    }

    const user = await prisma.user.findUnique({ where: { id: req.user!.userId } });
    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    const valid = await comparePassword(password, user.passwordHash);
    if (!valid) {
      res.status(401).json({ success: false, message: 'Incorrect password.' });
      return;
    }

    await prisma.user.update({
      where: { id: user.id },
      data: { twoFactorEnabled: false, twoFactorSecret: null },
    });

    res.json({ success: true, message: '2FA has been disabled.' });
  } catch (error) {
    console.error('[AUTH] Disable 2FA error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

export default router;
