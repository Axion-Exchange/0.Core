import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { prisma } from '../lib/db.js';
import { config } from '../config/index.js';
import { sha256 } from '../lib/crypto.js';
import { AuthenticationError, ConflictError, NotFoundError } from '../middleware/error.js';
import type { JwtPayload } from '../types/index.js';
import type { Admin } from '@prisma/client';

const SALT_ROUNDS = 12;
const MAX_FAILED_LOGINS = 5;
const LOCKOUT_DURATION_MS = 15 * 60 * 1000; // 15 minutes

export class AuthService {
  /**
   * Authenticate admin via email + password, return JWT.
   */
  async login(email: string, password: string, ipAddress: string, userAgent?: string) {
    const admin = await prisma.admin.findUnique({ where: { email } });

    if (!admin || !admin.isActive) {
      throw new AuthenticationError('Invalid credentials');
    }

    // Check lockout
    if (admin.lockedUntil && admin.lockedUntil > new Date()) {
      const remainingMs = admin.lockedUntil.getTime() - Date.now();
      const remainingMin = Math.ceil(remainingMs / 60000);
      throw new AuthenticationError(`Account locked. Try again in ${remainingMin} minutes.`);
    }

    const isValid = await bcrypt.compare(password, admin.passwordHash);

    if (!isValid) {
      // Increment failed logins
      const failedLogins = admin.failedLogins + 1;
      const update: Record<string, unknown> = { failedLogins };

      if (failedLogins >= MAX_FAILED_LOGINS) {
        update['lockedUntil'] = new Date(Date.now() + LOCKOUT_DURATION_MS);
      }

      await prisma.admin.update({
        where: { id: admin.id },
        data: update as any,
      });

      throw new AuthenticationError('Invalid credentials');
    }

    // Reset failed logins on success
    await prisma.admin.update({
      where: { id: admin.id },
      data: {
        failedLogins: 0,
        lockedUntil: null,
        lastLoginAt: new Date(),
        lastLoginIp: ipAddress,
      },
    });

    // Create session
    const sessionId = crypto.randomUUID();
    const payload: JwtPayload = {
      sub: admin.id,
      email: admin.email,
      role: admin.role,
      sessionId,
    };

    const token = jwt.sign(payload, config.JWT_SECRET, {
      expiresIn: config.JWT_EXPIRES_IN as any,
    });

    const tokenHash = sha256(token);
    const expiresAt = new Date(Date.now() + parseDuration(config.JWT_EXPIRES_IN));

    await prisma.session.create({
      data: {
        id: sessionId,
        adminId: admin.id,
        tokenHash,
        ipAddress,
        userAgent: userAgent ?? null,
        expiresAt,
      },
    });

    return {
      token,
      admin: sanitizeAdmin(admin),
      expiresAt,
    };
  }

  /**
   * Revoke a session (logout).
   */
  async logout(sessionId: string) {
    await prisma.session.update({
      where: { id: sessionId },
      data: { revokedAt: new Date() },
    }).catch(() => {
      // Session may not exist — that's fine
    });
  }

  /**
   * Get current admin profile.
   */
  async getProfile(adminId: string) {
    const admin = await prisma.admin.findUnique({
      where: { id: adminId },
    });

    if (!admin) throw new NotFoundError('Admin', adminId);
    return sanitizeAdmin(admin);
  }

  /**
   * Change admin password.
   */
  async changePassword(adminId: string, currentPassword: string, newPassword: string) {
    const admin = await prisma.admin.findUnique({ where: { id: adminId } });
    if (!admin) throw new NotFoundError('Admin', adminId);

    const isValid = await bcrypt.compare(currentPassword, admin.passwordHash);
    if (!isValid) throw new AuthenticationError('Current password is incorrect');

    const passwordHash = await bcrypt.hash(newPassword, SALT_ROUNDS);
    await prisma.admin.update({
      where: { id: adminId },
      data: { passwordHash },
    });

    // Revoke all sessions
    await prisma.session.updateMany({
      where: { adminId, revokedAt: null },
      data: { revokedAt: new Date() },
    });
  }

  /**
   * Create a new admin (SUPER_ADMIN only).
   */
  async createAdmin(data: { email: string; password: string; displayName: string; role?: string }) {
    const existing = await prisma.admin.findUnique({ where: { email: data.email } });
    if (existing) throw new ConflictError(`Admin with email '${data.email}' already exists`);

    const passwordHash = await bcrypt.hash(data.password, SALT_ROUNDS);

    const admin = await prisma.admin.create({
      data: {
        email: data.email,
        passwordHash,
        displayName: data.displayName,
        role: (data.role as any) ?? 'ANALYST',
      },
    });

    return sanitizeAdmin(admin);
  }

  /**
   * Hash a password (for seeding).
   */
  async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, SALT_ROUNDS);
  }
}

function sanitizeAdmin(admin: Admin) {
  const { passwordHash, mfaSecret, ...safe } = admin;
  return safe;
}

function parseDuration(duration: string): number {
  const match = duration.match(/^(\d+)(h|d|m|s)$/);
  if (!match) return 24 * 60 * 60 * 1000; // default 24h

  const value = parseInt(match[1]!, 10);
  switch (match[2]) {
    case 'h': return value * 60 * 60 * 1000;
    case 'd': return value * 24 * 60 * 60 * 1000;
    case 'm': return value * 60 * 1000;
    case 's': return value * 1000;
    default: return 24 * 60 * 60 * 1000;
  }
}

export const authService = new AuthService();
