import { Router, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { prisma } from '../config/database';
import { authenticateToken } from '../middleware/auth';
import { AuthenticatedRequest, GalleryItem, CreateGalleryRequest } from '../types';
import { logger } from '../config/logger';

const router = Router();

/**
 * @swagger
 * /galleries:
 *   get:
 *     summary: Get user's galleries
 *     tags: [Galleries]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Galleries retrieved successfully
 */
router.get('/', authenticateToken, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const galleries = await prisma.gallery.findMany({
      where: { userId: req.user!.id },
      include: {
        images: {
          include: {
            media: true
          },
          orderBy: { order: 'asc' }
        }
      },
      orderBy: { createdAt: 'desc' }
    });

    const formattedGalleries: GalleryItem[] = galleries.map(gallery => ({
      id: gallery.id,
      title: gallery.title,
      images: gallery.images.map(img => img.media.url),
      createdAt: gallery.createdAt.toISOString(),
    }));

    res.json(formattedGalleries);
  } catch (error) {
    logger.error('Get galleries error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to retrieve galleries'
      }
    });
  }
});

/**
 * @swagger
 * /galleries:
 *   post:
 *     summary: Create new gallery
 *     tags: [Galleries]
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
 *               images:
 *                 type: array
 *                 items:
 *                   type: string
 *     responses:
 *       201:
 *         description: Gallery created successfully
 */
router.post('/', [
  authenticateToken,
  body('title').trim().isLength({ min: 1 }),
  body('images').isArray().isLength({ min: 1 })
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

    const { title, images }: CreateGalleryRequest = req.body;

    // Verify that all image IDs belong to the user
    const mediaItems = await prisma.mediaItem.findMany({
      where: {
        id: { in: images },
        userId: req.user!.id,
        type: 'IMAGE'
      }
    });

    if (mediaItems.length !== images.length) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_IMAGES',
          message: 'One or more image IDs are invalid'
        }
      });
    }

    // Create gallery
    const gallery = await prisma.gallery.create({
      data: {
        title,
        userId: req.user!.id,
      }
    });

    // Add images to gallery
    await Promise.all(
      images.map((imageId, index) =>
        prisma.galleryMedia.create({
          data: {
            galleryId: gallery.id,
            mediaId: imageId,
            order: index
          }
        })
      )
    );

    // Fetch the complete gallery with images
    const completeGallery = await prisma.gallery.findUnique({
      where: { id: gallery.id },
      include: {
        images: {
          include: {
            media: true
          },
          orderBy: { order: 'asc' }
        }
      }
    });

    const formattedGallery: GalleryItem = {
      id: completeGallery!.id,
      title: completeGallery!.title,
      images: completeGallery!.images.map(img => img.media.url),
      createdAt: completeGallery!.createdAt.toISOString(),
    };

    res.status(201).json(formattedGallery);
    logger.info(`Gallery created: ${title} by ${req.user!.email}`);
  } catch (error) {
    logger.error('Create gallery error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to create gallery'
      }
    });
  }
});

export default router; 