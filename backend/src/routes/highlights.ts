import { Router, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { prisma } from '../config/database';
import { authenticateToken } from '../middleware/auth';
import { AuthenticatedRequest, HighlightReel, CreateHighlightRequest } from '../types';
import { logger } from '../config/logger';

const router = Router();

/**
 * @swagger
 * /highlights:
 *   get:
 *     summary: Get user's highlight reels
 *     tags: [Highlights]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Highlight reels retrieved successfully
 */
router.get('/', authenticateToken, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const highlights = await prisma.highlight.findMany({
      where: { userId: req.user!.id },
      include: {
        media: {
          include: {
            media: true
          },
          orderBy: { order: 'asc' }
        }
      },
      orderBy: { createdAt: 'desc' }
    });

    const formattedHighlights: HighlightItem[] = highlights.map(highlight => ({
      id: highlight.id,
      title: highlight.title,
      media: highlight.media.map(m => m.media.url),
      createdAt: highlight.createdAt.toISOString(),
    }));

    res.json(formattedHighlights);
  } catch (error) {
    logger.error('Get highlights error:', error);
    // Return empty array instead of error object to prevent frontend .map() errors
    res.status(200).json([]);
  }
});

/**
 * @swagger
 * /highlights:
 *   post:
 *     summary: Create new highlight reel
 *     tags: [Highlights]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               title:
 *                 type: string
 *               clips:
 *                 type: array
 *                 items:
 *                   type: string
 *               duration:
 *                 type: number
 *     responses:
 *       201:
 *         description: Highlight reel created successfully
 */
router.post('/', [
  authenticateToken,
  body('title').trim().isLength({ min: 1 }),
  body('clips').isArray().isLength({ min: 1 }),
  body('duration').isNumeric().isInt({ min: 1, max: 300 })
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

    const { title, clips, duration }: CreateHighlightRequest = req.body;

    // Verify that all clip IDs belong to the user and are videos
    const mediaItems = await prisma.mediaItem.findMany({
      where: {
        id: { in: clips },
        userId: req.user!.id,
        type: 'VIDEO'
      }
    });

    if (mediaItems.length !== clips.length) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_CLIPS',
          message: 'One or more video clip IDs are invalid'
        }
      });
    }

    // Create highlight reel
    const highlight = await prisma.highlightReel.create({
      data: {
        title,
        duration,
        userId: req.user!.id,
      }
    });

    // Add clips to highlight reel
    await Promise.all(
      clips.map((clipId, index) =>
        prisma.highlightMedia.create({
          data: {
            highlightReelId: highlight.id,
            mediaId: clipId,
            order: index
          }
        })
      )
    );

    // Fetch the complete highlight reel with clips
    const completeHighlight = await prisma.highlightReel.findUnique({
      where: { id: highlight.id },
      include: {
        clips: {
          include: {
            media: true
          },
          orderBy: { order: 'asc' }
        }
      }
    });

    const formattedHighlight: HighlightReel = {
      id: completeHighlight!.id,
      title: completeHighlight!.title,
      clips: completeHighlight!.clips.map(c => c.media.url),
      duration: completeHighlight!.duration,
      createdAt: completeHighlight!.createdAt.toISOString(),
    };

    res.status(201).json(formattedHighlight);
    logger.info(`Highlight reel created: ${title} by ${req.user!.email}`);
  } catch (error) {
    logger.error('Create highlight error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to create highlight reel'
      }
    });
  }
});

export default router; 