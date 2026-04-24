import { createLogger } from '../lib/logger.js';

const log = createLogger('pear-manager-service');

export interface PearStatus {
  isRunning: boolean;
  pid: number | null;
  uptimeSeconds: number;
  lastPing: Date | null;
}

export class PearManagerService {
  private readonly pearUrl: string;
  private readonly apiKey: string;
  private isOnline: boolean = false;
  private lastPingTime: Date | null = null;
  private pollingInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Determine the absolute path to the injected Python engine
    this.pearUrl = process.env.PEAR_API_URL || 'http://localhost:8000';
    this.apiKey = process.env.PEAR_API_SECRET_KEY || 'dev_secret_key';
    
    this.startHeartbeat();
  }

  /**
   * Health Check Monitor: Polls the FastAPI server to ensure it is alive.
   * This replaces the old child_process PID check.
   */
  private startHeartbeat() {
    this.pollingInterval = setInterval(async () => {
      try {
        const res = await fetch(`${this.pearUrl}/`, {
          headers: { 'Authorization': `Bearer ${this.apiKey}` },
        });
        
        if (res.ok) {
          this.isOnline = true;
          this.lastPingTime = new Date();
        } else {
          this.isOnline = false;
        }
      } catch (err) {
        this.isOnline = false;
      }
    }, 10000); // Check every 10 seconds
  }

  /**
   * Sends an HTTP request to PearV2 to begin automation.
   */
  public async start(): Promise<void> {
    log.info('Sending boot command to PearV2 Daemon via HTTP...');
    try {
      const res = await fetch(`${this.pearUrl}/api/v1/control/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.apiKey}` }
      });
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      log.info('PearV2 started successfully.');
    } catch (err: any) {
      log.error('Failed to start PearV2 via HTTP', { error: err.message });
      throw new Error(`Failed to contact PearV2 API: ${err.message}`);
    }
  }

  /**
   * Sends an HTTP request to PearV2 to stop automation safely.
   */
  public async stop(): Promise<void> {
    log.info('Executing shutdown sequence on PearV2 Daemon via HTTP...');
    try {
      const res = await fetch(`${this.pearUrl}/api/v1/control/stop`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.apiKey}` }
      });
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      log.info('PearV2 stopped successfully.');
    } catch (err: any) {
      log.error('Failed to stop PearV2 via HTTP', { error: err.message });
      throw new Error(`Failed to contact PearV2 API: ${err.message}`);
    }
  }

  /**
   * Status reporter for frontend orchestration.
   */
  public getStatus(): PearStatus {
    return {
      isRunning: this.isOnline,
      pid: null, // PID is no longer tracked natively in microservice pattern
      uptimeSeconds: 0, // This would optimally be fetched from the health check payload
      lastPing: this.lastPingTime
    };
  }

  /**
   * Overwrites the python .env remotely via the FastAPI config endpoint.
   */
  public async updateConfig(configs: Record<string, string>): Promise<void> {
    log.info('Sending config updates to PearV2 via HTTP...');
    try {
      const res = await fetch(`${this.pearUrl}/api/v1/config`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config: configs })
      });
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      log.info(`Updated PearV2 configuration mapping remotely.`);
    } catch (err: any) {
      log.error('Failed to write updated python .env remotely', { error: err.message });
      throw new Error('Failed to overwrite .env remotely');
    }
  }
}

export const pearManagerService = new PearManagerService();
