import { z } from 'zod';

export const documentUploadSchema = z.object({
  // Since we are parsing binary forms with multer, Zod validates other textual payload parameters.
  // Example: if we pass 'type' indicating PASSPORT or ID_CARD
  type: z.enum(['PASSPORT', 'ID_CARD', 'DRIVERS_LICENSE']).optional(),
});

export const amlScreeningSchema = z.object({
  forceRescreen: z.boolean().optional().default(false),
});
