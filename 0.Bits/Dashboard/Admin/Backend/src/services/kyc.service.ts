import { prisma } from '../lib/db.js';
import { NotFoundError } from '../middleware/error.js';
import { IKycProvider } from './kyc/provider.interface.js';
import { DiditProvider } from './kyc/didit.provider.js';

class KycService {
  private provider: IKycProvider;

  constructor() {
    // In the future this can be dynamic or set via ENV (e.g. process.env.KYC_PROVIDER)
    // Starting with Didit as per specs.
    this.provider = new DiditProvider();
  }

  async processIdVerification(userId: string, frontImage: Buffer, backImage?: Buffer) {
    const user = await prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new NotFoundError('User', userId);

    const result = await this.provider.verifyIdDocument(frontImage, backImage);

    // Update KYC Status
    let newStatus = user.kycStatus;
    if (result.status === 'APPROVED') newStatus = 'APPROVED';
    else if (result.status === 'REJECTED') newStatus = 'REJECTED';
    else if (result.status === 'REVIEW_NEEDED') newStatus = 'PENDING';

    await prisma.user.update({
      where: { id: userId },
      data: { kycStatus: newStatus as any },
    });

    return result;
  }

  async processLiveness(userId: string, faceImage: Buffer) {
    const user = await prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new NotFoundError('User', userId);

    const result = await this.provider.verifyLiveness(faceImage);
    return result;
  }

  async processAmlScreening(userId: string) {
    const user = await prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new NotFoundError('User', userId);

    // Parse names safely
    const parts = user.displayName.split(' ');
    const firstName = parts[0] || 'Unknown';
    const lastName = parts.slice(1).join(' ') || 'Unknown';

    const result = await this.provider.screenAML(firstName, lastName, undefined, user.country || undefined);

    if (result.isHit) {
      await prisma.user.update({
        where: { id: userId },
        data: { riskScore: 100, kycStatus: 'REJECTED' as any },
      });
    }

    return result;
  }
}

export const kycService = new KycService();
