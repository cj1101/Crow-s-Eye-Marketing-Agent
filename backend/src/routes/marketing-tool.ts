import { Router, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { prisma } from '../config/database';
import { authenticateToken } from '../middleware/auth';
import { AuthenticatedRequest, MarketingToolStats, CreatePostRequest, CreatePostResponse } from '../types';
import { logger } from '../config/logger';

const router = Router();

/**
 * @swagger
 * /marketing-tool/stats:
 *   get:
 *     summary: Get marketing tool statistics
 *     tags: [Marketing Tool]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Marketing tool stats retrieved successfully
 */
router.get('/stats', authenticateToken, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;

    // Get basic counts
    const [totalPosts, scheduledPosts, aiGenerated, mediaFiles, socialAccounts] = await Promise.all([
      prisma.post.count({ where: { userId } }),
      prisma.post.count({ where: { userId, scheduledFor: { not: null }, published: false } }),
      prisma.post.count({ where: { userId, content: { contains: '[AI Generated]' } } }),
      prisma.mediaItem.count({ where: { userId } }),
      3 // Mock value - would be from social accounts integration
    ]);

    // Get engagement rate
    const analyticsData = await prisma.postAnalytics.aggregate({
      where: { post: { userId } },
      _avg: { engagement: true }
    });

    // Get recent activity
    const recentActivities = await prisma.activity.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 10
    });

    const recentActivity = recentActivities.map(activity => ({
      id: activity.id,
      action: activity.action,
      timestamp: activity.createdAt.toISOString(),
      type: activity.type.toLowerCase() as 'success' | 'info' | 'warning'
    }));

    // Get user plan
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { plan: true }
    });

    const stats: MarketingToolStats = {
      totalPosts,
      scheduledPosts,
      aiGenerated,
      engagementRate: Math.round((analyticsData._avg.engagement || 0) * 100) / 100,
      socialAccounts,
      mediaFiles,
      recentActivity,
      subscriptionTier: user?.plan.toLowerCase() || 'free',
      aiCreditsRemaining: 100, // Mock value - would be tracked in subscription system
      aiEditsRemaining: 50      // Mock value - would be tracked in subscription system
    };

    res.json(stats);
  } catch (error) {
    logger.error('Get marketing tool stats error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to retrieve marketing tool statistics'
      }
    });
  }
});

/**
 * @swagger
 * /marketing-tool/posts:
 *   post:
 *     summary: Create new post
 *     tags: [Marketing Tool]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               content:
 *                 type: string
 *               platforms:
 *                 type: array
 *                 items:
 *                   type: string
 *               hashtags:
 *                 type: array
 *                 items:
 *                   type: string
 *               mediaFiles:
 *                 type: array
 *                 items:
 *                   type: string
 *               scheduledFor:
 *                 type: string
 *                 format: date-time
 *     responses:
 *       201:
 *         description: Post created successfully
 */
router.post('/posts', [
  authenticateToken,
  body('content').trim().isLength({ min: 1 }),
  body('platforms').isArray().isLength({ min: 1 }),
  body('hashtags').isArray(),
  body('mediaFiles').isArray(),
  body('scheduledFor').optional().isISO8601()
], async (req: AuthenticatedRequest, res: Response) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input',
          details: errors.array()
        }
      });
    }

    const { content, platforms, hashtags, mediaFiles, scheduledFor }: CreatePostRequest = req.body;

    // Verify that all media file IDs belong to the user (if any provided)
    if (mediaFiles.length > 0) {
      const mediaItems = await prisma.mediaItem.findMany({
        where: {
          id: { in: mediaFiles },
          userId: req.user!.id
        }
      });

      if (mediaItems.length !== mediaFiles.length) {
        return res.status(400).json({
          success: false,
          error: {
            code: 'INVALID_MEDIA',
            message: 'One or more media file IDs are invalid'
          }
        });
      }
    }

    // Create post
    const post = await prisma.post.create({
      data: {
        content,
        platforms,
        hashtags,
        scheduledFor: scheduledFor ? new Date(scheduledFor) : null,
        userId: req.user!.id,
      }
    });

    // Add media to post if provided
    if (mediaFiles.length > 0) {
      await Promise.all(
        mediaFiles.map((mediaId, index) =>
          prisma.postMedia.create({
            data: {
              postId: post.id,
              mediaId,
              order: index
            }
          })
        )
      );
    }

    // Log activity
    await prisma.activity.create({
      data: {
        userId: req.user!.id,
        action: scheduledFor ? 'Post scheduled' : 'Post created',
        type: 'SUCCESS'
      }
    });

    const response: CreatePostResponse = {
      success: true,
      postId: post.id
    };

    res.status(201).json(response);
    logger.info(`Post created: ${post.id} by ${req.user!.email}`);
  } catch (error) {
    logger.error('Create post error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to create post'
      }
    });
  }
});

export default router; 