import { Router, Request, Response } from 'express';
import { z } from 'zod';
import prisma from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import { authorize } from '../middleware/auth';
import { sendWithdrawalConfirmation } from '../lib/email';

const router = Router();

// ─── ADMIN ZOD SCHEMAS ───────────────────────────────────

const updateClientSchema = z.object({
  name: z.string().min(1).optional(),
  status: z.enum(['ACTIVE', 'INACTIVE', 'BLOCKED']).optional(),
  kycStatus: z.string().min(1).optional(),
  country: z.string().optional().nullable(),
  phone: z.string().optional().nullable(),
  company: z.string().optional().nullable(),
});

const approveTxSchema = z.object({
  adminNotes: z.string().optional(),
});

const rejectTxSchema = z.object({
  adminNotes: z.string().min(5, "Admin notes are required and must be at least 5 characters to reject a transaction."),
});

const updateTxSchema = z.object({
  amount: z.union([z.string(), z.number()]).optional().transform(v => (v ? Number(v) : undefined)),
  currency: z.string().min(2).max(10).optional(),
  status: z.enum(['PENDING', 'COMPLETED', 'FAILED', 'REJECTED', 'CANCELED']).optional(),
  adminNotes: z.string().optional().nullable(),
  reference: z.string().optional().nullable(),
});

const updatePoolSchema = z.object({
  name: z.string().min(1).optional(),
  apy: z.union([z.string(), z.number()]).optional().transform(v => (v ? Number(v) : undefined)),
  feeRate: z.union([z.string(), z.number()]).optional().transform(v => (v ? Number(v) : undefined)),
  totalTvl: z.union([z.string(), z.number()]).optional().transform(v => (v ? Number(v) : undefined)),
  isActive: z.boolean().optional(),
  description: z.string().optional().nullable(),
  cryptoDepositAddress: z.string().optional().nullable(),
  chain: z.string().min(1).optional(),
  riskTier: z.enum(['Low', 'Medium', 'High']).optional(),
});

// All admin routes require authentication + admin role
router.use(authenticate);
router.use(authorize('admin'));

// ─── GET /admin/dashboard ───────────────────────────────
// Admin KPI overview

router.get('/dashboard', async (req: Request, res: Response) => {
  try {
    const [
      totalUsers,
      activeUsers,
      pendingDeposits,
      pendingWithdrawals,
      totalTransactions,
      totalPositions,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.user.count({ where: { status: 'ACTIVE' } }),
      prisma.transaction.count({ where: { type: 'DEPOSIT', status: 'PENDING' } }),
      prisma.transaction.count({ where: { type: 'WITHDRAWAL', status: 'PENDING' } }),
      prisma.transaction.count(),
      prisma.position.count({ where: { status: 'ACTIVE' } }),
    ]);

    const totalTvl = await prisma.position.aggregate({
      where: { status: 'ACTIVE' },
      _sum: { currentValue: true },
    });

    const totalYield = await prisma.yield.aggregate({
      _sum: { amount: true },
    });

    const recentSignups = await prisma.user.findMany({
      orderBy: { createdAt: 'desc' },
      take: 5,
      select: { id: true, email: true, name: true, status: true, kycStatus: true, createdAt: true },
    });

    res.json({
      success: true,
      data: {
        kpi: {
          totalUsers,
          activeUsers,
          pendingDeposits,
          pendingWithdrawals,
          totalTransactions,
          totalPositions,
          totalTvl: Number(totalTvl._sum.currentValue || 0),
          totalYield: Number(totalYield._sum.amount || 0),
        },
        recentSignups,
      },
    });
  } catch (error) {
    console.error('[ADMIN] Dashboard error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /admin/clients ─────────────────────────────────

router.get('/clients', async (req: Request, res: Response) => {
  try {
    const { status, kycStatus, search, page = '1', perPage = '20' } = req.query;

    const where: any = { isTrashed: false };
    if (status) where.status = status;
    if (kycStatus) where.kycStatus = kycStatus;
    if (search) {
      where.OR = [
        { email: { contains: search as string, mode: 'insensitive' } },
        { name: { contains: search as string, mode: 'insensitive' } },
      ];
    }

    const skip = (parseInt(page as string, 10) - 1) * parseInt(perPage as string, 10);
    const take = parseInt(perPage as string, 10);

    const [clients, total] = await Promise.all([
      prisma.user.findMany({
        where,
        include: { role: { select: { slug: true, name: true } } },
        orderBy: { createdAt: 'desc' },
        skip,
        take,
      }),
      prisma.user.count({ where }),
    ]);

    res.json({
      success: true,
      data: {
        items: clients.map((u) => ({
          id: u.id,
          email: u.email,
          name: u.name,
          status: u.status,
          kycStatus: u.kycStatus,
          twoFactorEnabled: u.twoFactorEnabled,
          role: u.role.slug,
          country: u.country,
          phone: u.phone,
          company: u.company,
          createdAt: u.createdAt,
          lastSignInAt: u.lastSignInAt,
        })),
        total,
        page: parseInt(page as string, 10),
        perPage: take,
        totalPages: Math.ceil(total / take),
      },
    });
  } catch (error) {
    console.error('[ADMIN] List clients error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /admin/clients/:id ─────────────────────────────

router.get('/clients/:id', async (req: Request, res: Response) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.params.id as string },
      include: {
        role: true,
        positions: { include: { pool: true } },
        transactions: { orderBy: { createdAt: 'desc' }, take: 20 },
        whitelistedAddresses: true,
      },
    });

    if (!user) {
      res.status(404).json({ success: false, message: 'Client not found' });
      return;
    }

    res.json({ success: true, data: user });
  } catch (error) {
    console.error('[ADMIN] Get client error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── PUT /admin/clients/:id ─────────────────────────────

router.put('/clients/:id', async (req: Request, res: Response) => {
  try {
    const parsed = updateClientSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, message: 'Invalid data', errors: parsed.error.format() });
      return;
    }
    const updateData = parsed.data;

    const user = await prisma.user.findUnique({ where: { id: req.params.id as string } });
    if (!user) {
      res.status(404).json({ success: false, message: 'Client not found' });
      return;
    }

    if (Object.keys(updateData).length > 0) {
      const updated = await prisma.user.update({
        where: { id: user.id },
        data: updateData,
      });

      await prisma.systemLog.create({
        data: {
          event: 'ADMIN_CLIENT_EDIT',
          userId: req.user!.userId,
          entityId: user.id,
          entityType: 'user',
          description: `Admin edited client ${user.email}: ${JSON.stringify(updateData)}`,
          ipAddress: req.ip || 'unknown',
        },
      });

      res.json({ success: true, data: updated });
    } else {
      res.json({ success: true, data: user });
    }
  } catch (error) {
    console.error('[ADMIN] Edit client error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /admin/transactions ────────────────────────────

router.get('/transactions', async (req: Request, res: Response) => {
  try {
    const { status, type, userId, page = '1', perPage = '25' } = req.query;

    const where: any = {};
    if (status) where.status = status;
    if (type) where.type = type;
    if (userId) where.userId = userId;

    const skip = (parseInt(page as string, 10) - 1) * parseInt(perPage as string, 10);
    const take = parseInt(perPage as string, 10);

    const [transactions, total] = await Promise.all([
      prisma.transaction.findMany({
        where,
        include: {
          user: { select: { id: true, email: true, name: true } },
          pool: { select: { id: true, name: true } },
        },
        orderBy: [{ status: 'asc' }, { createdAt: 'desc' }], // PENDING first
        skip,
        take,
      }),
      prisma.transaction.count({ where }),
    ]);

    res.json({
      success: true,
      data: {
        items: transactions.map((tx) => ({
          id: tx.id,
          type: tx.type,
          amount: Number(tx.amount),
          currency: tx.currency,
          status: tx.status,
          reference: tx.reference,
          paymentMethod: tx.paymentMethod,
          cryptoCoin: tx.cryptoCoin,
          cryptoNetwork: tx.cryptoNetwork,
          cryptoTxHash: tx.cryptoTxHash,
          destinationAddress: tx.destinationAddress,
          adminNotes: tx.adminNotes,
          processedBy: tx.processedBy,
          processedAt: tx.processedAt,
          user: tx.user,
          pool: tx.pool,
          createdAt: tx.createdAt,
        })),
        total,
        page: parseInt(page as string, 10),
        perPage: take,
        totalPages: Math.ceil(total / take),
      },
    });
  } catch (error) {
    console.error('[ADMIN] List transactions error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── PUT /admin/transactions/:id/approve ────────────────

router.put('/transactions/:id/approve', async (req: Request, res: Response) => {
  try {
    const parsed = approveTxSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, message: 'Invalid data', errors: parsed.error.format() });
      return;
    }
    const { adminNotes } = parsed.data;

    const tx = await prisma.transaction.findUnique({
      where: { id: req.params.id as string },
      include: { user: true, pool: true },
    });

    if (!tx) {
      res.status(404).json({ success: false, message: 'Transaction not found' });
      return;
    }

    if (tx.status !== 'PENDING') {
      res.status(400).json({ success: false, message: `Cannot approve a ${tx.status} transaction.` });
      return;
    }

    // Update transaction status
    const updated = await prisma.transaction.update({
      where: { id: tx.id },
      data: {
        status: 'COMPLETED',
        processedBy: req.user!.userId,
        processedAt: new Date(),
        adminNotes: adminNotes || tx.adminNotes,
      },
    });

    // If deposit: create or update position
    if (tx.type === 'DEPOSIT' && tx.poolId) {
      const existingPosition = await prisma.position.findUnique({
        where: { userId_poolId: { userId: tx.userId, poolId: tx.poolId } },
      });

      if (existingPosition) {
        await prisma.position.update({
          where: { id: existingPosition.id },
          data: {
            investedAmount: { increment: Number(tx.amount) },
            currentValue: { increment: Number(tx.amount) },
          },
        });
      } else {
        await prisma.position.create({
          data: {
            userId: tx.userId,
            poolId: tx.poolId,
            investedAmount: Number(tx.amount),
            currentValue: Number(tx.amount),
            currency: tx.currency,
            status: 'ACTIVE',
          },
        });
      }
    }

    // If withdrawal: send confirmation email
    if (tx.type === 'WITHDRAWAL') {
      await sendWithdrawalConfirmation(
        tx.user.email,
        Number(tx.amount).toLocaleString('en-US', { minimumFractionDigits: 2 }),
        tx.currency,
        tx.destinationAddress || 'N/A',
      );
    }

    // Audit log
    await prisma.systemLog.create({
      data: {
        event: `ADMIN_${tx.type}_APPROVED`,
        userId: req.user!.userId,
        entityId: tx.id,
        entityType: 'transaction',
        description: `Admin approved ${tx.type} #${tx.reference || tx.id.slice(0, 8)} for ${tx.amount} ${tx.currency}. User: ${tx.user.email}`,
        ipAddress: req.ip || 'unknown',
      },
    });

    res.json({ success: true, data: updated, message: `${tx.type} approved successfully.` });
  } catch (error) {
    console.error('[ADMIN] Approve transaction error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── PUT /admin/transactions/:id/reject ─────────────────

router.put('/transactions/:id/reject', async (req: Request, res: Response) => {
  try {
    const parsed = rejectTxSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, message: parsed.error.errors[0].message });
      return;
    }
    const { adminNotes } = parsed.data;

    const tx = await prisma.transaction.findUnique({
      where: { id: req.params.id as string },
      include: { user: true },
    });

    if (!tx) {
      res.status(404).json({ success: false, message: 'Transaction not found' });
      return;
    }

    if (tx.status !== 'PENDING') {
      res.status(400).json({ success: false, message: `Cannot reject a ${tx.status} transaction.` });
      return;
    }

    const updated = await prisma.transaction.update({
      where: { id: tx.id },
      data: {
        status: 'REJECTED',
        processedBy: req.user!.userId,
        processedAt: new Date(),
        adminNotes,
      },
    });

    // Audit log
    await prisma.systemLog.create({
      data: {
        event: `ADMIN_${tx.type}_REJECTED`,
        userId: req.user!.userId,
        entityId: tx.id,
        entityType: 'transaction',
        description: `Admin rejected ${tx.type} #${tx.reference || tx.id.slice(0, 8)}: ${adminNotes}. User: ${tx.user.email}`,
        ipAddress: req.ip || 'unknown',
      },
    });

    res.json({ success: true, data: updated, message: `${tx.type} rejected.` });
  } catch (error) {
    console.error('[ADMIN] Reject transaction error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── PUT /admin/transactions/:id ────────────────────────
// Edit transaction fields (amount, notes, status)

router.put('/transactions/:id', async (req: Request, res: Response) => {
  try {
    const parsed = updateTxSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, message: 'Invalid data', errors: parsed.error.format() });
      return;
    }
    const updateData = parsed.data;

    const tx = await prisma.transaction.findUnique({ where: { id: req.params.id as string } });
    if (!tx) {
      res.status(404).json({ success: false, message: 'Transaction not found' });
      return;
    }

    if (Object.keys(updateData).length > 0) {
      const updated = await prisma.transaction.update({
        where: { id: tx.id },
        data: updateData,
      });

      await prisma.systemLog.create({
        data: {
          event: 'ADMIN_TRANSACTION_EDIT',
          userId: req.user!.userId,
          entityId: tx.id,
          entityType: 'transaction',
          description: `Admin edited transaction ${tx.reference || tx.id.slice(0, 8)}: ${JSON.stringify(updateData)}`,
          ipAddress: req.ip || 'unknown',
        },
      });

      res.json({ success: true, data: updated });
    } else {
       res.json({ success: true, data: tx });
    }
  } catch (error) {
    console.error('[ADMIN] Edit transaction error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /admin/pools ───────────────────────────────────

router.get('/pools', async (req: Request, res: Response) => {
  try {
    const pools = await prisma.pool.findMany({
      include: {
        _count: { select: { positions: true, transactions: true } },
      },
      orderBy: { id: 'asc' },
    });

    res.json({
      success: true,
      data: pools.map((p) => ({
        id: p.id,
        name: p.name,
        chain: p.chain,
        riskTier: p.riskTier,
        apy: Number(p.apy),
        feeRate: Number(p.feeRate),
        totalTvl: Number(p.totalTvl),
        volume24h: Number(p.volume24h),
        icon: p.icon,
        description: p.description,
        isActive: p.isActive,
        cryptoDepositAddress: p.cryptoDepositAddress,
        positionCount: p._count.positions,
        transactionCount: p._count.transactions,
        createdAt: p.createdAt,
      })),
    });
  } catch (error) {
    console.error('[ADMIN] List pools error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── PUT /admin/pools/:id ───────────────────────────────

router.put('/pools/:id', async (req: Request, res: Response) => {
  try {
    const poolId = parseInt(req.params.id as string, 10);
    const parsed = updatePoolSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, message: 'Invalid data', errors: parsed.error.format() });
      return;
    }
    const updateData = parsed.data;

    const pool = await prisma.pool.findUnique({ where: { id: poolId } });
    if (!pool) {
      res.status(404).json({ success: false, message: 'Pool not found' });
      return;
    }

    if (Object.keys(updateData).length > 0) {
      const updated = await prisma.pool.update({
        where: { id: poolId },
        data: updateData,
      });

      await prisma.systemLog.create({
        data: {
          event: 'ADMIN_POOL_EDIT',
          userId: req.user!.userId,
          entityId: poolId.toString(),
          entityType: 'pool',
          description: `Admin edited pool "${pool.name}": ${JSON.stringify(updateData)}`,
          ipAddress: req.ip || 'unknown',
        },
      });

      res.json({ success: true, data: updated });
    } else {
      res.json({ success: true, data: pool });
    }
  } catch (error) {
    console.error('[ADMIN] Edit pool error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /admin/logs ────────────────────────────────────

router.get('/logs', async (req: Request, res: Response) => {
  try {
    const { event, userId, entityType, page = '1', perPage = '50' } = req.query;

    const where: any = {};
    if (event) where.event = { contains: event as string, mode: 'insensitive' };
    if (userId) where.userId = userId;
    if (entityType) where.entityType = entityType;

    const skip = (parseInt(page as string, 10) - 1) * parseInt(perPage as string, 10);
    const take = parseInt(perPage as string, 10);

    const [logs, total] = await Promise.all([
      prisma.systemLog.findMany({
        where,
        include: { user: { select: { email: true, name: true } } },
        orderBy: { createdAt: 'desc' },
        skip,
        take,
      }),
      prisma.systemLog.count({ where }),
    ]);

    res.json({
      success: true,
      data: {
        items: logs,
        total,
        page: parseInt(page as string, 10),
        perPage: take,
        totalPages: Math.ceil(total / take),
      },
    });
  } catch (error) {
    console.error('[ADMIN] List logs error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

export default router;
