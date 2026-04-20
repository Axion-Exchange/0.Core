import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs/promises';
import { createLogger } from '../lib/logger.js';

const log = createLogger('pear-manager-service');

export interface PearStatus {
  isRunning: boolean;
  pid: number | null;
  uptimeSeconds: number;
}

export class PearManagerService {
  private child: ChildProcess | null = null;
  private readonly enginePath: string;
  private startTime: number | null = null;

  constructor() {
    // Determine the absolute path to the injected Python engine
    this.enginePath = path.resolve(process.cwd(), 'p2p-engine');
  }

  /**
   * Spawns the main.py python orchestrator if not already active.
   */
  public async start(): Promise<void> {
    if (this.child && !this.child.killed) {
      log.warn('PearV2 is already running. Ignoring start command.');
      return;
    }

    log.info(`Booting PearV2 Python Daemon from: ${this.enginePath}`);

    // Adjusting spawn to hit main.py. Ensure your node environment has python3 installed.
    // Recommended to use venv in production, but here we assume globally available python3.
    this.child = spawn('python3', ['main.py'], {
      cwd: this.enginePath,
      env: { ...process.env, PYTHONPATH: this.enginePath }, // Pass current ENV downward
      stdio: 'pipe',
    });

    this.startTime = Date.now();

    this.child.stdout?.on('data', (data) => {
      // Stream python stdout natively to backend logger
      const output = data.toString().trim();
      if (output) log.debug(`[PearV2] ${output}`);
    });

    this.child.stderr?.on('data', (data) => {
      const output = data.toString().trim();
      if (output) log.error(`[PearV2 ERR] ${output}`);
    });

    this.child.on('close', (code) => {
      log.warn(`PearV2 python daemon exited with code ${code}`);
      this.child = null;
      this.startTime = null;
    });
  }

  /**
   * Gracefully kills the python daemon.
   */
  public stop(): void {
    if (this.child && !this.child.killed) {
      log.info('Executing shutdown sequence on PearV2 Daemon...');
      this.child.kill('SIGTERM');
      this.child = null;
      this.startTime = null;
    } else {
      log.info('PearV2 is not running.');
    }
  }

  /**
   * Status reporter for frontend orchestration.
   */
  public getStatus(): PearStatus {
    const isRunning = this.child !== null && !this.child.killed;
    return {
      isRunning,
      pid: isRunning ? this.child!.pid || null : null,
      uptimeSeconds: isRunning && this.startTime ? Math.floor((Date.now() - this.startTime) / 1000) : 0,
    };
  }

  /**
   * Overwrites the python .env natively for configuration.
   * This bridges the Node Dashboard to the Python memory.
   */
  public async updateConfig(configs: Record<string, string>): Promise<void> {
    const envPath = path.join(this.enginePath, '.env');
    let currentEnv = '';

    try {
      currentEnv = await fs.readFile(envPath, 'utf8');
    } catch (e: any) {
      // File doesn't exist, ignore and create fresh
      if (e.code !== 'ENOENT') {
        log.error('Failed to read python .env', { error: e });
        throw new Error('Failed to read python .env');
      }
    }

    // Process old lines and update matching configs
    const lines = currentEnv.split('\n');
    const updatedKeys = new Set<string>();
    
    const newLines = lines.map(line => {
      const [key] = line.split('=');
      const trimmedKey = key?.trim();
      if (trimmedKey && configs[trimmedKey] !== undefined) {
        updatedKeys.add(trimmedKey);
        return `${trimmedKey}="${configs[trimmedKey]}"`;
      }
      return line;
    });

    // Append new configs not found in previous .env
    for (const [key, val] of Object.entries(configs)) {
      if (!updatedKeys.has(key)) {
        newLines.push(`${key}="${val}"`);
      }
    }

    try {
      await fs.writeFile(envPath, newLines.join('\n'), 'utf8');
      log.info(`Updated PearV2 configuration mapping internally.`);
    } catch (e) {
      log.error('Failed to write updated python .env', { error: e });
      throw new Error('Failed to overwrite .env');
    }
  }
}

export const pearManagerService = new PearManagerService();
