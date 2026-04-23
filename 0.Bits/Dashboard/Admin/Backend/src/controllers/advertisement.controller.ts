import { Request, Response, NextFunction } from 'express';
import { advertisementService } from '../services/advertisement.service.js';
import { sendSuccess } from '../lib/response.js';
import { z } from 'zod';
import { ValidationError } from '../middleware/error.js';

export const getAdvertisementsHandler = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const ads = await advertisementService.listAds();
    sendSuccess(res, ads);
  } catch (error) {
    next(error);
  }
};

const updateStatusSchema = z.object({
  status: z.enum(['Active', 'Paused'])
});

export const patchAdvertisementStatusHandler = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params.id as string;
    
    const parsed = updateStatusSchema.safeParse(req.body);
    if (!parsed.success) {
      throw new ValidationError('Invalid status payload');
    }

    // Attempt to pull admin ID from auth middleware if available
    const adminId = (req as any).user?.id || (req as any).admin?.id;

    const updatedAd = await advertisementService.toggleAd(id, parsed.data.status, adminId);
    
    sendSuccess(res, updatedAd);
  } catch (error) {
    next(error);
  }
};
