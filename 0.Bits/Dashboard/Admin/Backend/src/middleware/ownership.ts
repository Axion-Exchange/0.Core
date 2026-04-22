import type { Request, Response, NextFunction } from "express";
import { sendError } from "../lib/response.js";
import { createLogger } from "../lib/logger.js";

const log = createLogger("ownership");

/**
 * BOLA Protection — Broken Object Level Authorization guard.
 *
 * Doc ref: OWASP API Security Top 10 (citation 36)
 * "The most common institutional vulnerability is BOLA, where a user
 *  can access another user's data by manipulating an ID in the request."
 *
 * This middleware ensures that admin users can only access resources
 * they have permission for. For SUPER_ADMIN, all access is granted.
 * For regular ADMIN, access is restricted to their own resources
 * unless the endpoint is explicitly flagged as shared.
 *
 * Usage:
 *   router.get("/users/:id", requireAuth, ownershipGuard("ADMIN"), handler);
 */

/**
 * Ownership guard factory.
 * Allows SUPER_ADMIN unrestricted access.
 * For specified roles, validates that req.params.id matches req.admin.sub
 * unless the route is a list/aggregate endpoint.
 */
export function ownershipGuard(...restrictedRoles: string[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.admin) {
      sendError(res, 401, "AUTH_MISSING", "Authentication required");
      return;
    }

    // SUPER_ADMIN bypasses all ownership checks
    if (req.admin.role === "SUPER_ADMIN") {
      next();
      return;
    }

    // If the admin role is in the restricted list, validate ownership
    if (restrictedRoles.includes(req.admin.role)) {
      const resourceId = req.params.id || req.params.userId;

      // List endpoints (no specific resource ID) are allowed
      if (!resourceId) {
        next();
        return;
      }

      // Check if the admin is accessing their own resource
      if (resourceId !== req.admin.sub) {
        log.warn(
          `[BOLA] Admin ${req.admin.sub} (${req.admin.role}) attempted to access resource ${resourceId}`
        );
        sendError(
          res,
          403,
          "FORBIDDEN",
          "You do not have permission to access this resource"
        );
        return;
      }
    }

    next();
  };
}

/**
 * Audit trail middleware — logs all resource access for compliance.
 * Attaches to sensitive endpoints to create an access audit trail.
 */
export function auditAccess(resourceType: string) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    if (req.admin) {
      const resourceId = req.params.id || req.params.userId || "list";
      log.info(
        `[AuditAccess] ${req.admin.sub} (${req.admin.role}) accessed ${resourceType}/${resourceId} via ${req.method} ${req.originalUrl}`
      );
    }
    next();
  };
}
