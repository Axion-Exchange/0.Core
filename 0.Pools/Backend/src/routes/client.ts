import { Router, Request, Response } from 'express';
import prisma from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = Router();

// All routes require authentication
router.use(authenticate);

// ─── GET /client/settings/withdrawals ───────────────────

router.get('/settings/withdrawals', async (req: Request, res: Response) => {
  try {
    const addresses = await prisma.whitelistedAddress.findMany({
      where: { userId: req.user!.userId },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ success: true, data: addresses });
  } catch (error) {
    console.error('[CLIENT] Get withdrawal addresses error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /client/settings/withdrawals ──────────────────

router.post('/settings/withdrawals', async (req: Request, res: Response) => {
  try {
    const { type, asset, networkOrBank, address } = req.body;

    if (!type || !address) {
      res.status(400).json({ success: false, message: 'Type and address are required.' });
      return;
    }

    // Validation
    if (type === 'crypto') {
      const btcRegex = /^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,39}$/;
      const ethRegex = /^0x[a-fA-F0-9]{40}$/;
      const trxRegex = /^T[a-zA-Z0-9]{33}$/;
      
      let isValidCrypto = false;
      if (asset === 'BTC' && btcRegex.test(address)) isValidCrypto = true;
      if (asset === 'ETH' && ethRegex.test(address)) isValidCrypto = true;
      if (asset === 'USDT' && (ethRegex.test(address) || trxRegex.test(address))) isValidCrypto = true;
      if (asset === 'USDC' && (ethRegex.test(address) || trxRegex.test(address))) isValidCrypto = true;
      if (asset === 'SOL') isValidCrypto = true; // Placeholder for SOL

      if (!isValidCrypto && networkOrBank !== 'other') {
        res.status(400).json({ success: false, message: 'Invalid crypto address format for the specified asset.' });
        return;
      }
    } else if (type === 'fiat') {
      const ibanRegex = /^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$/;
      if (!ibanRegex.test(address.replace(/\s/g, ''))) {
        res.status(400).json({ success: false, message: 'Invalid IBAN format.' });
        return;
      }
    }

    // Check for duplicate
    const existing = await prisma.whitelistedAddress.findFirst({
      where: { userId: req.user!.userId, address, type },
    });

    if (existing) {
      res.status(409).json({ success: false, message: 'This address is already registered.' });
      return;
    }

    const entry = await prisma.whitelistedAddress.create({
      data: {
        userId: req.user!.userId,
        type: type || 'crypto',
        asset: asset || (type === 'fiat' ? 'EUR' : 'USDC'),
        networkOrBank: networkOrBank || '',
        address,
        verified: false,
      },
    });

    // Log the event
    await prisma.systemLog.create({
      data: {
        event: 'WITHDRAWAL_ADDRESS_ADDED',
        userId: req.user!.userId,
        entityId: entry.id,
        entityType: 'whitelisted_address',
        description: `Added ${type} withdrawal address: ${address.slice(0, 10)}...`,
        ipAddress: req.ip || 'unknown',
      },
    });

    res.status(201).json({ success: true, data: entry });
  } catch (error) {
    console.error('[CLIENT] Add withdrawal address error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── DELETE /client/settings/withdrawals/:id ────────────

router.delete('/settings/withdrawals/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const address = await prisma.whitelistedAddress.findFirst({
      where: { id: id as string, userId: req.user!.userId },
    });

    if (!address) {
      res.status(404).json({ success: false, message: 'Address not found.' });
      return;
    }

    await prisma.whitelistedAddress.delete({ where: { id: address.id } });

    res.json({ success: true, message: 'Address removed.' });
  } catch (error) {
    console.error('[CLIENT] Delete withdrawal address error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /client/dashboard ──────────────────────────────
// Returns user KYC status + account overview

router.get('/dashboard', async (req: Request, res: Response) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user!.userId },
      select: {
        id: true,
        email: true,
        name: true,
        kycStatus: true,
        twoFactorEnabled: true,
        status: true,
        createdAt: true,
      },
    });

    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    res.json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          kycStatus: user.kycStatus,
          twoFactorEnabled: user.twoFactorEnabled,
          status: user.status,
          createdAt: user.createdAt,
        },
      },
    });
  } catch (error) {
    console.error('[CLIENT] Dashboard error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── POST /client/kyc/verify ────────────────────────────
// Trigger KYC verification (placeholder — would integrate with Didit/SumSub)

router.post('/kyc/verify', async (req: Request, res: Response) => {
  try {
    // In production: trigger Didit OAuth flow and process callback
    // For now: transition from PENDING → IN_REVIEW
    const user = await prisma.user.findUnique({ where: { id: req.user!.userId } });
    if (!user) {
      res.status(404).json({ success: false, message: 'User not found' });
      return;
    }

    const newStatus = user.kycStatus === 'PENDING' ? 'IN_REVIEW' : user.kycStatus;

    await prisma.user.update({
      where: { id: user.id },
      data: { kycStatus: newStatus },
    });

    await prisma.systemLog.create({
      data: {
        event: 'KYC_VERIFICATION_INITIATED',
        userId: user.id,
        description: `KYC verification initiated. Status: ${newStatus}`,
        ipAddress: req.ip || 'unknown',
      },
    });

    res.json({
      success: true,
      data: { status: newStatus },
      message: 'KYC verification has been initiated.',
    });
  } catch (error) {
    console.error('[CLIENT] KYC verify error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /client/transactions/export ────────────────────
// CSV export of transaction ledger with date range filtering

router.get('/transactions/export', async (req: Request, res: Response) => {
  try {
    const { startDate, endDate } = req.query;

    const where: any = { userId: req.user!.userId };
    if (startDate || endDate) {
      where.createdAt = {};
      if (startDate) where.createdAt.gte = new Date(startDate as string);
      if (endDate) where.createdAt.lte = new Date(endDate as string);
    }

    const transactions = await prisma.transaction.findMany({
      where,
      include: { pool: { select: { name: true } } },
      orderBy: { createdAt: 'desc' },
      take: 10000, // Safety limit
    });

    // Build CSV
    const headers = 'Reference,Type,Amount,Currency,Status,Pool,Payment Method,Date\n';
    const rows = transactions.map((tx) =>
      [
        tx.reference || tx.id.slice(0, 8),
        tx.type,
        tx.amount.toString(),
        tx.currency,
        tx.status,
        tx.pool?.name || 'N/A',
        tx.paymentMethod || 'N/A',
        tx.createdAt.toISOString(),
      ].join(',')
    ).join('\n');

    const csv = headers + rows;

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="0pools_Ledger_Export_${new Date().toISOString().slice(0, 10)}.csv"`);
    res.send(csv);
  } catch (error) {
    console.error('[CLIENT] CSV export error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

export default router;
