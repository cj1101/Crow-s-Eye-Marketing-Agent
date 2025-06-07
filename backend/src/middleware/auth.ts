import { Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { env } from '../config/environment';
import { prisma } from '../config/database';
import { AuthenticatedRequest, JWTPayload, UserProfile } from '../types';
import { logger } from '../config/logger';

export const authenticateToken = (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({
      success: false,
      error: {
        code: 'NO_TOKEN',
        message: 'Access token is required'
      }
    });
  }

  jwt.verify(token, env.JWT_SECRET, async (err: any, decoded: any) => {
    if (err) {
      logger.warn('Token verification failed:', { error: err.message });
      return res.status(403).json({
        success: false,
        error: {
          code: 'INVALID_TOKEN',
          message: 'Invalid or expired token'
        }
      });
    }

    try {
      // Get user from database
      const user = await prisma.user.findUnique({
        where: { id: decoded.userId },
        select: {
          id: true,
          email: true,
          displayName: true,
          plan: true,
          isActive: true
        }
      });

      if (!user || !user.isActive) {
        return res.status(403).json({
          success: false,
          error: {
            code: 'USER_NOT_FOUND',
            message: 'User not found or inactive'
          }
        });
      }

      req.user = user;
      next();
    } catch (error) {
      logger.error('Database error during authentication:', error);
      return res.status(500).json({
        success: false,
        error: {
          code: 'AUTH_ERROR',
          message: 'Authentication failed'
        }
      });
    }
  });
};

export const optionalAuth = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
) => {
  try {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
      return next();
    }

    const decoded = jwt.verify(token, env.JWT_SECRET) as JWTPayload;
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        email: true,
        displayName: true,
        firstName: true,
        lastName: true,
        avatar: true,
        plan: true,
        createdAt: true,
        lastLoginAt: true,
      }
    });

    if (user) {
      const userProfile: UserProfile = {
        id: user.id,
        email: user.email,
        displayName: user.displayName,
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        avatar: user.avatar || undefined,
        plan: user.plan.toLowerCase() as 'free' | 'creator' | 'pro',
        createdAt: user.createdAt.toISOString(),
        lastLoginAt: user.lastLoginAt?.toISOString() || user.createdAt.toISOString(),
      };

      req.user = userProfile;
    }

    next();
  } catch (error) {
    // If optional auth fails, just continue without user
    next();
  }
}; 