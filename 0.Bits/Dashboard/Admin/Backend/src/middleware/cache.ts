/**
 * HTTP Cache Middleware
 * 
 * Adds Cache-Control headers to API responses to enable browser-level
 * caching. This reduces redundant network requests and improves
 * perceived performance for institutional dashboard users.
 */
import { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';

/**
 * Combined Cache-Control + ETag middleware.
 * Intercepts res.json() to:
 * 1. Override Helmet's no-store with a proper Cache-Control directive
 * 2. Generate an ETag from the response body
 * 3. Return 304 Not Modified if client already has current data
 * 
 * @param maxAgeSeconds - Browser cache duration in seconds (default 30)
 */
export function httpCacheWithEtag(maxAgeSeconds: number = 30) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const originalJson = res.json.bind(res);
    
    res.json = function(body: any) {
      // 1. Override Helmet's Cache-Control right before sending
      res.setHeader('Cache-Control', `private, max-age=${maxAgeSeconds}, must-revalidate`);
      res.removeHeader('Pragma');
      res.removeHeader('Surrogate-Control');
      
      // 2. Generate ETag
      const bodyStr = JSON.stringify(body);
      const hash = crypto.createHash('md5').update(bodyStr).digest('hex').slice(0, 16);
      const etag = `"${hash}"`;
      
      // 3. Conditional: return 304 if client already has this version
      const clientEtag = req.headers['if-none-match'];
      if (clientEtag === etag) {
        res.status(304).end();
        return res;
      }
      
      res.setHeader('ETag', etag);
      return originalJson(body);
    };
    
    next();
  };
}

// Legacy exports for backward compat
export const httpCache = (maxAge: number) => httpCacheWithEtag(maxAge);
export const etagMiddleware = (_req: Request, _res: Response, next: NextFunction) => next();
