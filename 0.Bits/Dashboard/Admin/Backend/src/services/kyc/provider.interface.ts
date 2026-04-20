export interface IKycProvider {
  /**
   * Identifies the provider uniquely (e.g. 'DIDIT', 'SUMUP')
   */
  get name(): string;

  /**
   * Standalone ID Verification.
   * Expects binary buffers of ID documents.
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

  /**
   * Biometric Age Estimation from a face image.
   */
  estimateAge(faceImage: Buffer): Promise<KycResult>;

  /**
   * Match two faces to see if they belong to the same person.
   */
  matchFaces(image1: Buffer, image2: Buffer): Promise<KycResult>;

  /**
   * Search an existing database of faces for a matching face.
   */
  searchFace(faceImage: Buffer): Promise<KycResult>;

  /**
   * Verify an email address natively.
   */
  verifyEmail(email: string): Promise<KycResult>;

  /**
   * Verify a phone number natively.
   */
  verifyPhone(phone: string): Promise<KycResult>;

  /**
   * Create an automated Onboarding Session (if the provider supports UI-hosted sessions).
   */
  createSession(payload: Record<string, any>): Promise<KycSessionResult>;

  /**
   * Get the status of an onboarding session.
   */
  getSession(sessionId: string): Promise<KycSessionResult>;
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

export interface KycSessionResult {
  success: boolean;
  sessionId: string;
  sessionUrl?: string;
  status: 'INITIALIZED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'EXPIRED';
  metadata?: Record<string, any>;
}
