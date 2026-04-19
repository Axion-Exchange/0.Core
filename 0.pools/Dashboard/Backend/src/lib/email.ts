import nodemailer from 'nodemailer';

// ─── EMAIL CONFIGURATION ────────────────────────────────
// In production: use AWS SES or any SMTP provider
// Set these env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: parseInt(process.env.SMTP_PORT || '587', 10),
  secure: process.env.SMTP_SECURE === 'true',
  auth: {
    user: process.env.SMTP_USER || '',
    pass: process.env.SMTP_PASS || '',
  },
});

const FROM_ADDRESS = process.env.SMTP_FROM || 'noreply@0pool.io';
const BRAND_NAME = '0pool.io';

// ─── SEND FUNCTIONS ─────────────────────────────────────

export async function sendPasswordResetOTP(email: string, code: string): Promise<boolean> {
  try {
    if (!process.env.SMTP_USER) {
      console.log(`[EMAIL] (dev-mode) Password reset OTP for ${email}: ${code}`);
      return true;
    }

    await transporter.sendMail({
      from: `${BRAND_NAME} <${FROM_ADDRESS}>`,
      to: email,
      subject: `${BRAND_NAME} — Password Reset Code`,
      html: `
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
          <h2 style="color: #fff; background: #0a0a0a; padding: 24px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
            <span style="color: #00FF66;">0pool</span>.io
          </h2>
          <p style="color: #333; font-size: 15px;">Your password reset verification code is:</p>
          <div style="background: #f8f9fa; border: 2px solid #00FF66; border-radius: 12px; padding: 24px; text-align: center; margin: 20px 0;">
            <span style="font-size: 36px; font-weight: 800; letter-spacing: 8px; font-family: monospace; color: #0a0a0a;">${code}</span>
          </div>
          <p style="color: #666; font-size: 13px;">This code expires in <strong>15 minutes</strong>. If you didn't request this, ignore this email.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
          <p style="color: #999; font-size: 11px; text-align: center;">0pools · Institutional Liquidity Infrastructure</p>
        </div>
      `,
    });

    console.log(`[EMAIL] Password reset OTP sent to ${email}`);
    return true;
  } catch (error) {
    console.error('[EMAIL] Failed to send password reset OTP:', error);
    return false;
  }
}

export async function sendEmailVerification(email: string, verifyUrl: string): Promise<boolean> {
  try {
    if (!process.env.SMTP_USER) {
      console.log(`[EMAIL] (dev-mode) Verification URL for ${email}: ${verifyUrl}`);
      return true;
    }

    await transporter.sendMail({
      from: `${BRAND_NAME} <${FROM_ADDRESS}>`,
      to: email,
      subject: `${BRAND_NAME} — Verify Your Email`,
      html: `
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
          <h2 style="color: #fff; background: #0a0a0a; padding: 24px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
            <span style="color: #00FF66;">0pool</span>.io
          </h2>
          <p style="color: #333; font-size: 15px;">Welcome to ${BRAND_NAME}. Please verify your email address:</p>
          <div style="text-align: center; margin: 28px 0;">
            <a href="${verifyUrl}" style="background: #00FF66; color: #0a0a0a; padding: 14px 40px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
              Verify Email
            </a>
          </div>
          <p style="color: #666; font-size: 13px;">This link expires in 24 hours. If you didn't create an account, ignore this email.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
          <p style="color: #999; font-size: 11px; text-align: center;">0pools · Institutional Liquidity Infrastructure</p>
        </div>
      `,
    });

    console.log(`[EMAIL] Verification email sent to ${email}`);
    return true;
  } catch (error) {
    console.error('[EMAIL] Failed to send verification email:', error);
    return false;
  }
}

export async function sendWithdrawalConfirmation(email: string, amount: string, currency: string, destination: string): Promise<boolean> {
  try {
    if (!process.env.SMTP_USER) {
      console.log(`[EMAIL] (dev-mode) Withdrawal confirmation for ${email}: ${amount} ${currency} → ${destination}`);
      return true;
    }

    await transporter.sendMail({
      from: `${BRAND_NAME} <${FROM_ADDRESS}>`,
      to: email,
      subject: `${BRAND_NAME} — Withdrawal Processed`,
      html: `
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
          <h2 style="color: #fff; background: #0a0a0a; padding: 24px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
            <span style="color: #00FF66;">0pool</span>.io
          </h2>
          <p style="color: #333; font-size: 15px;">Your withdrawal has been processed:</p>
          <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <table style="width: 100%; font-size: 14px; color: #333;">
              <tr><td style="padding: 6px 0; color: #999;">Amount</td><td style="text-align: right; font-weight: 700;">${amount} ${currency}</td></tr>
              <tr><td style="padding: 6px 0; color: #999;">Destination</td><td style="text-align: right; font-family: monospace; font-size: 12px;">${destination.slice(0, 20)}...</td></tr>
            </table>
          </div>
          <p style="color: #666; font-size: 13px;">If you did not authorize this withdrawal, contact support immediately.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
          <p style="color: #999; font-size: 11px; text-align: center;">0pools · Institutional Liquidity Infrastructure</p>
        </div>
      `,
    });

    return true;
  } catch (error) {
    console.error('[EMAIL] Failed to send withdrawal confirmation:', error);
    return false;
  }
}

export async function sendLoginAlert(email: string, ip: string, device: string, location: string): Promise<boolean> {
  try {
    if (!process.env.SMTP_USER) {
      console.log(`[EMAIL] (dev-mode) Login alert for ${email}: IP=${ip}, Device=${device}`);
      return true;
    }

    await transporter.sendMail({
      from: `${BRAND_NAME} <${FROM_ADDRESS}>`,
      to: email,
      subject: `${BRAND_NAME} — New Login Detected`,
      html: `
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
          <h2 style="color: #fff; background: #0a0a0a; padding: 24px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
            <span style="color: #00FF66;">0pool</span>.io
          </h2>
          <p style="color: #333; font-size: 15px;">A new login was detected on your account:</p>
          <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <table style="width: 100%; font-size: 14px; color: #333;">
              <tr><td style="padding: 6px 0; color: #999;">IP Address</td><td style="text-align: right; font-family: monospace;">${ip}</td></tr>
              <tr><td style="padding: 6px 0; color: #999;">Device</td><td style="text-align: right;">${device}</td></tr>
              <tr><td style="padding: 6px 0; color: #999;">Location</td><td style="text-align: right;">${location}</td></tr>
              <tr><td style="padding: 6px 0; color: #999;">Time</td><td style="text-align: right;">${new Date().toISOString()}</td></tr>
            </table>
          </div>
          <p style="color: #e53e3e; font-size: 13px; font-weight: 600;">If this wasn't you, change your password immediately and enable 2FA.</p>
        </div>
      `,
    });

    return true;
  } catch (error) {
    console.error('[EMAIL] Failed to send login alert:', error);
    return false;
  }
}
