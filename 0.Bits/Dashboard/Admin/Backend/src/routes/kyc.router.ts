import { Router } from 'express';
import { kycService } from '../services/kyc.service.js';
import { sendSuccess } from '../lib/response.js';
import { requireAuth } from '../middleware/auth.js';
import { validateBody } from '../middleware/validate.js';
import { amlScreeningSchema } from '../validators/kyc.schema.js';
import multer from 'multer';

// Use memory storage for standalone verification (buffer passes straight to Didit provider)
// Files will NOT touch the physical disk.
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit per image
});

export const kycRouter = Router();

kycRouter.use(requireAuth);

/**
 * Handle Primary ID Documents (Front + Back)
 */
kycRouter.post(
  '/:id/id-document',
  upload.fields([
    { name: 'document_front', maxCount: 1 },
    { name: 'document_back', maxCount: 1 },
  ]),
  async (req, res, next) => {
    try {
      const files = req.files as { [fieldname: string]: Express.Multer.File[] };
      const front = files['document_front']?.[0]?.buffer;
      const back = files['document_back']?.[0]?.buffer;

      if (!front) {
        res.status(400).json({ error: 'document_front is required' });
        return;
      }

      const id = req.params.id as string;
      const result = await kycService.processIdVerification(id, front, back);
      sendSuccess(res, result);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * Handle Passive Liveness (Selfie Video/Image)
 */
kycRouter.post(
  '/:id/liveness',
  upload.single('face_image'),
  async (req, res, next) => {
    try {
      const file = req.file?.buffer;
      if (!file) {
        res.status(400).json({ error: 'face_image is required' });
        return;
      }

      const id = req.params.id as string;
      const result = await kycService.processLiveness(id, file);
      sendSuccess(res, result);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * Trigger AML Screening Text Query
 */
kycRouter.post(
  '/:id/aml',
  validateBody(amlScreeningSchema),
  async (req, res, next) => {
    try {
      const id = req.params.id as string;
      const result = await kycService.processAmlScreening(id);
      sendSuccess(res, result);
    } catch (error) {
      next(error);
    }
  }
);
