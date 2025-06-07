import { Router, Response } from 'express';
import { prisma } from '../config/database';
import { authenticateToken } from '../middleware/auth';
import { AuthenticatedRequest, AnalyticsResponse } from '../types';
import { logger } from '../config/logger';

const router = Router();

/**
 * @swagger
 * /analytics:
 *   get:
 *     summary: Get analytics data
 *     tags: [Analytics]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Analytics data retrieved successfully
 */
router.get('/', authenticateToken, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;

    // Get aggregate analytics data
    const totalPosts = await prisma.post.count({
      where: { userId }
    });

    const analyticsData = await prisma.postAnalytics.aggregate({
      where: {
        post: { userId }
      },
      _sum: {
        views: true,
        likes: true,
        comments: true,
        shares: true
      },
      _avg: {
        engagement: true
      }
    });

    // Get top posts
    const topPostsData = await prisma.postAnalytics.findMany({
      where: {
        post: { userId }
      },
      include: {
        post: {
          select: {
            id: true,
            content: true
          }
        }
      },
      orderBy: {
        views: 'desc'
      },
      take: 5
    });

    const topPosts = topPostsData.map(item => ({
      id: item.post.id,
      title: item.post.content.substring(0, 50) + '...',
      views: item.views,
      likes: item.likes,
      platform: item.platform
    }));

    // Get platform stats
    const platformStatsData = await prisma.postAnalytics.groupBy({
      by: ['platform'],
      where: {
        post: { userId }
      },
      _count: {
        id: true
      },
      _avg: {
        engagement: true
      }
    });

    const platformStats = platformStatsData.map(item => ({
      platform: item.platform,
      posts: item._count.id,
      engagement: Math.round((item._avg.engagement || 0) * 100) / 100
    }));

    const analytics: AnalyticsResponse = {
      totalPosts,
      totalViews: analyticsData._sum.views || 0,
      totalLikes: analyticsData._sum.likes || 0,
      totalComments: analyticsData._sum.comments || 0,
      engagementRate: Math.round((analyticsData._avg.engagement || 0) * 100) / 100,
      topPosts,
      platformStats
    };

    res.json(analytics);
  } catch (error) {
    logger.error('Get analytics error:', error);
    // Return default analytics with empty arrays to prevent frontend .map() errors
    const fallbackAnalytics: AnalyticsResponse = {
      totalPosts: 0,
      totalViews: 0,
      totalLikes: 0,
      totalComments: 0,
      engagementRate: 0,
      topPosts: [],
      platformStats: []
    };
    res.status(200).json(fallbackAnalytics);
  }
});

export default router; 