import { Router, Request, Response } from 'express';
import prisma from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = Router();

router.use(authenticate);

// ─── GET /client/notifications ──────────────────────────
// Returns real notifications for the user based on their activity

router.get('/', async (req: Request, res: Response) => {
  try {
    const userId = req.user!.userId;
    const { page = '1', perPage = '20' } = req.query;
    const skip = (parseInt(page as string, 10) - 1) * parseInt(perPage as string, 10);
    const take = parseInt(perPage as string, 10);

    // Fetch recent transactions as notifications
    const transactions = await prisma.transaction.findMany({
      where: { userId },
      include: { pool: { select: { name: true } } },
      orderBy: { updatedAt: 'desc' },
      skip,
      take,
    });

    // Fetch recent yield payments
    const yields = await prisma.yield.findMany({
      where: { userId },
      include: { pool: { select: { name: true } } },
      orderBy: { date: 'desc' },
      take: 5,
    });

    // Build notification items
    const notifications: any[] = [];

    for (const tx of transactions) {
      let title = '';
      let message = '';
      let icon = 'transaction';
      let variant = 'default';

      switch (tx.type) {
        case 'DEPOSIT':
          if (tx.status === 'COMPLETED') {
            title = 'Deposit Confirmed';
            message = `Your ${tx.currency === 'EUR' ? '€' : '$'}${Number(tx.amount).toLocaleString()} deposit ${tx.pool ? `to ${tx.pool.name}` : ''} has been confirmed.`;
            icon = 'deposit';
            variant = 'success';
          } else if (tx.status === 'PENDING') {
            title = 'Deposit Pending';
            message = `Your ${tx.currency === 'EUR' ? '€' : '$'}${Number(tx.amount).toLocaleString()} deposit is being processed.`;
            icon = 'deposit';
            variant = 'warning';
          } else if (tx.status === 'REJECTED') {
            title = 'Deposit Rejected';
            message = tx.adminNotes || `Your deposit of ${tx.currency === 'EUR' ? '€' : '$'}${Number(tx.amount).toLocaleString()} was rejected.`;
            icon = 'alert';
            variant = 'destructive';
          }
          break;
        case 'WITHDRAWAL':
          if (tx.status === 'COMPLETED') {
            title = 'Withdrawal Processed';
            message = `${tx.currency === 'EUR' ? '€' : '$'}${Number(tx.amount).toLocaleString()} has been sent to ${tx.destinationAddress?.slice(0, 12) || 'your account'}...`;
            icon = 'withdrawal';
            variant = 'success';
          } else if (tx.status === 'PENDING') {
            title = 'Withdrawal Under Review';
            message = `Your withdrawal of ${tx.currency === 'EUR' ? '€' : '$'}${Number(tx.amount).toLocaleString()} is pending admin approval.`;
            icon = 'withdrawal';
            variant = 'warning';
          } else if (tx.status === 'REJECTED') {
            title = 'Withdrawal Rejected';
            message = tx.adminNotes || `Your withdrawal was rejected by compliance.`;
            icon = 'alert';
            variant = 'destructive';
          }
          break;
        case 'YIELD':
          title = 'Yield Credited';
          message = `${tx.currency === 'EUR' ? '€' : '$'}${Number(tx.amount).toLocaleString()} yield credited ${tx.pool ? `from ${tx.pool.name}` : ''}.`;
          icon = 'yield';
          variant = 'success';
          break;
      }

      if (title) {
        notifications.push({
          id: tx.id,
          title,
          message,
          icon,
          variant,
          reference: tx.reference,
          timestamp: tx.updatedAt,
          read: tx.status !== 'PENDING', // Unread = pending items
        });
      }
    }

    // Add yield notifications
    for (const y of yields) {
      notifications.push({
        id: y.id,
        title: 'Yield Payment',
        message: `$${Number(y.amount).toFixed(2)} yield earned from ${y.pool.name}.`,
        icon: 'yield',
        variant: 'success',
        timestamp: y.date,
        read: true,
      });
    }

    // Sort by timestamp
    notifications.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    const unreadCount = notifications.filter((n) => !n.read).length;

    res.json({
      success: true,
      data: {
        items: notifications.slice(0, take),
        unreadCount,
        total: notifications.length,
      },
    });
  } catch (error) {
    console.error('[NOTIFICATIONS] Error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

export default router;
