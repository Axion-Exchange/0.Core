import { Router, Request, Response } from 'express';
import prisma from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import { hashPassword, comparePassword } from '../lib/auth';

const router = Router();

// All routes require authentication
router.use(authenticate);

// ─── GET /user-management/account/settings ──────────────

router.get('/account/settings', async (req: Request, res: Response) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user!.userId },
      include: { role: true },
    });

    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    const [firstName, ...lastParts] = (user.name || '').split(' ');

    res.json({
      success: true,
      data: {
        user: {
          firstName: firstName || '',
          lastName: lastParts.join(' ') || '',
          avatarUrl: user.avatar || '',
          company: user.company || '',
          phone: user.phone || '',
          dateOfBirth: user.dateOfBirth?.toISOString() || null,
          email: user.email,
          location: user.country || '',
          bio: '',
          twoFactorEnabled: user.twoFactorEnabled,
        },
        settings: {
          theme: 'dark',
          language: 'en',
          timezone: user.timezone || 'UTC',
          currency: 'EUR',
          notificationPrefs: { sms: false, push: true, email: true },
          privacyPrefs: { showEmail: false, showPhone: false, allowIndexing: false, profileVisibility: 'private' },
          transparentSidebar: false,
          autoRefresh: true,
        },
      },
    });
  } catch (error) {
    console.error('[USER-MGMT] Get settings error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── PUT /user-management/account/settings ──────────────

router.put('/account/settings', async (req: Request, res: Response) => {
  try {
    const { userConfig, settingsConfig } = req.body;

    const updateData: any = {};

    if (userConfig) {
      if (userConfig.firstName !== undefined || userConfig.lastName !== undefined) {
        updateData.name = `${userConfig.firstName || ''} ${userConfig.lastName || ''}`.trim();
      }
      if (userConfig.company !== undefined) updateData.company = userConfig.company;
      if (userConfig.phone !== undefined) updateData.phone = userConfig.phone;
      if (userConfig.dateOfBirth !== undefined) updateData.dateOfBirth = new Date(userConfig.dateOfBirth);
      if (userConfig.avatarUrl !== undefined) updateData.avatar = userConfig.avatarUrl;
    }

    if (settingsConfig) {
      if (settingsConfig.timezone !== undefined) updateData.timezone = settingsConfig.timezone;
    }

    await prisma.user.update({
      where: { id: req.user!.userId },
      data: updateData,
    });

    res.json({ success: true, message: 'Settings saved successfully.' });
  } catch (error) {
    console.error('[USER-MGMT] Save settings error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── PUT /user-management/account/password ──────────────

router.put('/account/password', async (req: Request, res: Response) => {
  try {
    const { currentPassword, newPassword } = req.body;

    if (!currentPassword || !newPassword) {
      res.status(400).json({ success: false, message: 'Both current and new passwords are required.' });
      return;
    }

    if (newPassword.length < 8) {
      res.status(400).json({ success: false, message: 'New password must be at least 8 characters.' });
      return;
    }

    const user = await prisma.user.findUnique({ where: { id: req.user!.userId } });
    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    if (user.lockedUntil && user.lockedUntil > new Date()) {
      res.status(403).json({ success: false, message: 'Account locked due to excessive failed attempts. Try again later.' });
      return;
    }

    const isValid = await comparePassword(currentPassword, user.passwordHash);
    
    // Artificial latency to mitigate timing attacks
    await new Promise((resolve) => setTimeout(resolve, 600 + Math.random() * 400));

    if (!isValid) {
      const newAttempts = (user.failedLoginAttempts || 0) + 1;
      let updateData: any = { failedLoginAttempts: newAttempts };
      
      if (newAttempts >= 5) {
        // 24 hour lockout
        updateData.lockedUntil = new Date(Date.now() + 24 * 60 * 60 * 1000);
      }

      await prisma.user.update({
        where: { id: user.id },
        data: updateData,
      });

      res.status(401).json({ success: false, message: 'Current password is incorrect.' });
      return;
    }

    const hash = await hashPassword(newPassword);
    await prisma.user.update({
      where: { id: user.id },
      data: { 
        passwordHash: hash,
        failedLoginAttempts: 0,
        lockedUntil: null
      },
    });

    res.json({ success: true, message: 'Password updated successfully.' });
  } catch (error) {
    console.error('[USER-MGMT] Password change error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /user-management/security-sessions ─────────────

router.get('/security-sessions', async (req: Request, res: Response) => {
  try {
    const sessions = await prisma.session.findMany({
      where: { userId: req.user!.userId, expires: { gt: new Date() } },
      orderBy: { lastActive: 'desc' },
    });

    const currentToken = req.cookies.sessionToken || '';

    const data = sessions.map((s) => ({
      id: s.id,
      device: s.device || 'Unknown Device',
      os: s.os || 'Unknown OS',
      browser: s.browser || 'Unknown Browser',
      ip: s.ipAddress || '0.0.0.0',
      location: s.location || 'Unknown',
      isCurrent: s.sessionToken === currentToken,
      lastActive: s.lastActive?.toISOString() || s.expires.toISOString(),
    }));

    res.json({ success: true, data });
  } catch (error) {
    console.error('[USER-MGMT] Get sessions error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── DELETE /user-management/security-sessions/:id ──────

router.delete('/security-sessions/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const session = await prisma.session.findFirst({
      where: { id: id as string, userId: req.user!.userId },
    });

    if (!session) {
      res.status(404).json({ success: false, message: 'Session not found.' });
      return;
    }

    if (session.sessionToken === req.cookies.sessionToken) {
        res.clearCookie('sessionToken');
    }

    await prisma.session.delete({ where: { id: session.id } });

    res.json({ success: true, message: 'Session terminated.' });
  } catch (error) {
    console.error('[USER-MGMT] Delete session error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── DELETE /user-management/security-sessions ──────────
// End all other sessions (keep current)

router.delete('/security-sessions', async (req: Request, res: Response) => {
  try {
    const currentToken = req.cookies.sessionToken || '';

    await prisma.session.deleteMany({
      where: {
        userId: req.user!.userId,
        sessionToken: { not: currentToken },
      },
    });

    res.json({ success: true, message: 'All other sessions terminated.' });
  } catch (error) {
    console.error('[USER-MGMT] Delete all sessions error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

export default router;
