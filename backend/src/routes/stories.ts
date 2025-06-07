import { Router, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { prisma } from '../config/database';
import { authenticateToken } from '../middleware/auth';
import { AuthenticatedRequest, Story, CreateStoryRequest } from '../types';
import { logger } from '../config/logger';

const router = Router();

/**
 * @swagger
 * /stories:
 *   get:
 *     summary: Get user's stories
 *     tags: [Stories]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Stories retrieved successfully
 */
router.get('/', authenticateToken, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const stories = await prisma.story.findMany({
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

    const formattedStories: StoryItem[] = stories.map(story => ({
      id: story.id,
      title: story.title,
      content: story.content,
      media: story.media.map(m => m.media.url),
      createdAt: story.createdAt.toISOString(),
    }));

    res.json(formattedStories);
  } catch (error) {
    logger.error('Get stories error:', error);
    // Return empty array instead of error object to prevent frontend .map() errors
    res.status(200).json([]);
  }
});

/**
 * @swagger
 * /stories:
 *   post:
 *     summary: Create new story
 *     tags: [Stories]
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
 *               content:
 *                 type: string
 *               media:
 *                 type: array
 *                 items:
 *                   type: string
 *     responses:
 *       201:
 *         description: Story created successfully
 */
router.post('/', [
  authenticateToken,
  body('title').trim().isLength({ min: 1 }),
  body('content').trim().isLength({ min: 1 }),
  body('media').isArray()
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

    const { title, content, media }: CreateStoryRequest = req.body;

    // Verify that all media IDs belong to the user (if any provided)
    if (media.length > 0) {
      const mediaItems = await prisma.mediaItem.findMany({
        where: {
          id: { in: media },
          userId: req.user!.id
        }
      });

      if (mediaItems.length !== media.length) {
        return res.status(400).json({
          success: false,
          error: {
            code: 'INVALID_MEDIA',
            message: 'One or more media IDs are invalid'
          }
        });
      }
    }

    // Create story
    const story = await prisma.story.create({
      data: {
        title,
        content,
        userId: req.user!.id,
      }
    });

    // Add media to story if provided
    if (media.length > 0) {
      await Promise.all(
        media.map((mediaId, index) =>
          prisma.storyMedia.create({
            data: {
              storyId: story.id,
              mediaId,
              order: index
            }
          })
        )
      );
    }

    // Fetch the complete story with media
    const completeStory = await prisma.story.findUnique({
      where: { id: story.id },
      include: {
        media: {
          include: {
            media: true
          },
          orderBy: { order: 'asc' }
        }
      }
    });

    const formattedStory: Story = {
      id: completeStory!.id,
      title: completeStory!.title,
      content: completeStory!.content,
      media: completeStory!.media.map(m => m.media.url),
      createdAt: completeStory!.createdAt.toISOString(),
    };

    res.status(201).json(formattedStory);
    logger.info(`Story created: ${title} by ${req.user!.email}`);
  } catch (error) {
    logger.error('Create story error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to create story'
      }
    });
  }
});

export default router; 