import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

// Strict environment variable typing
const JWT_SECRET = process.env.JWT_SECRET || 'institutional-fallback-secret-rotation-required';

interface JwtPayload {
  userId: string;
  role: 'CLIENT' | 'ADMIN' | 'SUPER_ADMIN';
}

declare global {
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

export const requireAuth = (req: Request, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or malformed Authorization header' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as JwtPayload;
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(403).json({ error: 'Cryptographic signature invalid or token expired' });
  }
};

export const requireRole = (allowedRoles: JwtPayload['role'][]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user || !allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient institutional clearance (RBAC rejection)' });
    }
    next();
  };
};
