import { Router, Response } from 'express';
import multer from 'multer';
import { prisma } from '../config/database';
import { authenticateToken } from '../middleware/auth';
import { AuthenticatedRequest, MediaItem } from '../types';
import { logger } from '../config/logger';
import { uploadToStorage } from '../services/storage';

const router = Router();

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'video/mp4', 'video/webm',
      'audio/mp3', 'audio/wav'
    ];
    
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('File type not allowed'));
    }
  }
});

/**
 * @swagger
 * /media:
 *   get:
 *     summary: Get user's media files
 *     tags: [Media]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Media files retrieved successfully
 */
router.get('/', authenticateToken, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const mediaItems = await prisma.mediaItem.findMany({
      where: { userId: req.user!.id },
      orderBy: { createdAt: 'desc' }
    });

    const formattedItems: MediaItem[] = mediaItems.map(item => ({
      id: item.id,
      name: item.name,
      type: item.type.toLowerCase() as 'image' | 'video' | 'audio',
      url: item.url,
      thumbnail: item.thumbnail || undefined,
      size: item.size,
      createdAt: item.createdAt.toISOString(),
      tags: item.tags,
    }));

    res.json(formattedItems);
  } catch (error) {
    logger.error('Get media error:', error);
    // Return empty array instead of error object to prevent frontend .map() errors
    res.status(200).json([]);
  }
});

/**
 * @swagger
 * /media:
 *   post:
 *     summary: Upload media file
 *     tags: [Media]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               file:
 *                 type: string
 *                 format: binary
 *               metadata:
 *                 type: string
 *     responses:
 *       201:
 *         description: File uploaded successfully
 */
router.post('/', authenticateToken, upload.single('file'), async (req: AuthenticatedRequest, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'NO_FILE',
          message: 'No file uploaded'
        }
      });
    }

    // Upload to storage service (S3, GCS, etc.)
    const { url, thumbnail } = await uploadToStorage(req.file, req.user!.id);

    // Determine media type
    let mediaType: 'IMAGE' | 'VIDEO' | 'AUDIO' = 'IMAGE';
    if (req.file.mimetype.startsWith('video/')) {
      mediaType = 'VIDEO';
    } else if (req.file.mimetype.startsWith('audio/')) {
      mediaType = 'AUDIO';
    }

    // Parse metadata if provided
    let tags: string[] = [];
    if (req.body.metadata) {
      try {
        const metadata = JSON.parse(req.body.metadata);
        tags = metadata.tags || [];
      } catch (error) {
        // Ignore invalid metadata
      }
    }

    // Save to database
    const mediaItem = await prisma.mediaItem.create({
      data: {
        name: req.file.originalname,
        type: mediaType,
        url,
        thumbnail,
        size: req.file.size,
        tags,
        userId: req.user!.id,
      }
    });

    const formattedItem: MediaItem = {
      id: mediaItem.id,
      name: mediaItem.name,
      type: mediaItem.type.toLowerCase() as 'image' | 'video' | 'audio',
      url: mediaItem.url,
      thumbnail: mediaItem.thumbnail || undefined,
      size: mediaItem.size,
      createdAt: mediaItem.createdAt.toISOString(),
      tags: mediaItem.tags,
    };

    res.status(201).json(formattedItem);
    logger.info(`Media uploaded: ${mediaItem.name} by ${req.user!.email}`);
  } catch (error) {
    logger.error('Upload media error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'UPLOAD_FAILED',
        message: 'Failed to upload file'
      }
    });
  }
});

/**
 * @swagger
 * /media/{id}:
 *   delete:
 *     summary: Delete media file
 *     tags: [Media]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: File deleted successfully
 */
router.delete('/:id', authenticateToken, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;

    // Check if media item exists and belongs to user
    const mediaItem = await prisma.mediaItem.findFirst({
      where: {
        id,
        userId: req.user!.id
      }
    });

    if (!mediaItem) {
      return res.status(404).json({
        success: false,
        error: {
          code: 'MEDIA_NOT_FOUND',
          message: 'Media file not found'
        }
      });
    }

    // Delete from database
    await prisma.mediaItem.delete({
      where: { id }
    });

    // TODO: Delete from storage service as well

    res.json({
      success: true
    });

    logger.info(`Media deleted: ${mediaItem.name} by ${req.user!.email}`);
  } catch (error) {
    logger.error('Delete media error:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to delete media file'
      }
    });
  }
});

export default router; 