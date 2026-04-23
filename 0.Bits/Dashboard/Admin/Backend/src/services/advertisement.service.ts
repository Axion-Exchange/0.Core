import { prisma } from '../lib/db.js';
import { binanceService } from './binance.service.js';
import { getSocket } from '../lib/socket.js';
import { createLogger } from '../lib/logger.js';
import { NotFoundError, ValidationError } from '../middleware/error.js';

const log = createLogger('advertisement-service');

export class AdvertisementService {
  /**
   * Retrieves all advertisements from the database.
   */
  async listAds() {
    return prisma.p2PAdvertisement.findMany({
      orderBy: { createdAt: 'desc' },
      include: { account: true }
    });
  }

  /**
   * Toggles the ad status both on Binance and locally.
   */
  async toggleAd(id: string, status: 'Active' | 'Paused', adminId?: string) {
    const ad = await prisma.p2PAdvertisement.findUnique({
      where: { id },
      include: { account: true }
    });

    if (!ad) {
      throw new NotFoundError('Advertisement', id);
    }

    if (!ad.externalAdId) {
      throw new ValidationError('Advertisement is not linked to a Binance external ID');
    }

    // 1. Call Binance
    const success = await binanceService.toggleAdStatus(ad.externalAdId, status, ad.account);
    
    if (!success) {
      throw new Error(`Failed to toggle advertisement ${ad.externalAdId} on Binance`);
    }

    // 2. Update Prisma DB
    const updated = await prisma.p2PAdvertisement.update({
      where: { id },
      data: { status: status === 'Active' ? 'ACTIVE' : 'PAUSED' }
    });

    log.info(`[AdvertisementService] Ad ${ad.externalAdId} status changed to ${status} by Admin: ${adminId || 'System'}`);

    // 3. Emit websocket update globally
    try {
      const io = getSocket();
      io.emit('ad:update', {
        id: updated.id,
        externalAdId: updated.externalAdId,
        status: updated.status
      });
    } catch (err) {
      log.warn('[AdvertisementService] Could not emit ad:update socket event');
    }

    return updated;
  }
}

export const advertisementService = new AdvertisementService();
