export interface IKycProvider {
  /**
   * Identifies the provider uniquely (e.g. 'DIDIT', 'SUMUP')
   */
  get name(): string;

  /**
   * Standalone ID Verification.
   * Expects binary buffers (or base64 strings depending on implementation) of ID documents.
   */
  verifyIdDocument(frontImage: Buffer, backImage?: Buffer): Promise<KycResult>;

  /**
   * Standalone Passive Liveness checking a selfie against fraud vectors.
   */
  verifyLiveness(faceImage: Buffer): Promise<KycResult>;

  /**
   * Standalone AML Screening for sanctions/PEP matching via text data.
   */
  screenAML(firstName: string, lastName: string, dob?: string, country?: string): Promise<AmlResult>;

  /**
   * Database Validation for checking national ID text/numbers natively against gov registries.
   */
  verifyDatabase(country: string, documentType: string, documentNumber: string): Promise<KycResult>;

  /**
   * Standalone Proof of Address verification using an image of a utility bill or bank statement.
   */
  verifyProofOfAddress(addressDocument: Buffer): Promise<KycResult>;
}

export interface KycResult {
  success: boolean;
  status: 'APPROVED' | 'REJECTED' | 'REVIEW_NEEDED';
  decisionReason?: string;
  providerReferenceId: string;
  metadata?: Record<string, any>;
}

export interface AmlResult {
  success: boolean;
  isHit: boolean;          // True if there is a match in an AML database
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  providerReferenceId: string;
  metadata?: Record<string, any>;
}
