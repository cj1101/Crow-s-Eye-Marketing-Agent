import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

import { env, isDevelopment } from './config/environment';
import { connectDatabase, disconnectDatabase, healthCheck } from './config/database';
import { logger } from './config/logger';

// Import routes
import authRoutes from './routes/auth';
import userRoutes from './routes/user';
import mediaRoutes from './routes/media';
import analyticsRoutes from './routes/analytics';
import galleriesRoutes from './routes/galleries';
import storiesRoutes from './routes/stories';
import highlightsRoutes from './routes/highlights';
import marketingToolRoutes from './routes/marketing-tool';

const app = express();

// Trust proxy for rate limiting and CORS
app.set('trust proxy', 1);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  crossOriginEmbedderPolicy: false,
}));

// CORS configuration
const corsOptions = {
  origin: env.CORS_ORIGINS.split(',').map(origin => origin.trim()),
  credentials: true,
  optionsSuccessStatus: 200,
};
app.use(cors(corsOptions));

// Rate limiting
const limiter = rateLimit({
  windowMs: env.RATE_LIMIT_WINDOW_MS,
  max: env.RATE_LIMIT_MAX_REQUESTS,
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Too many requests from this IP, please try again later.'
    }
  },
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging middleware
if (isDevelopment) {
  app.use(morgan('dev'));
} else {
  app.use(morgan('combined', {
    stream: {
      write: (message: string) => {
        logger.info(message.trim());
      }
    }
  }));
}

// Swagger configuration
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Crow\'s Eye Marketing Suite API',
      version: '1.0.0',
      description: 'A comprehensive REST API for the Crow\'s Eye social media management platform',
      contact: {
        name: 'API Support',
        email: 'support@crowseye.tech'
      },
    },
    servers: [
      {
        url: isDevelopment ? `http://localhost:${env.PORT}` : 'https://api.crowseye.tech',
        description: isDevelopment ? 'Development server' : 'Production server',
      },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
    },
  },
  apis: ['./src/routes/*.ts'], // paths to files containing OpenAPI definitions
};

const specs = swaggerJsdoc(swaggerOptions);
app.use('/docs', swaggerUi.serve, swaggerUi.setup(specs, {
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: 'Crow\'s Eye API Documentation'
}));

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const dbHealth = await healthCheck();
    const status = dbHealth ? 'healthy' : 'unhealthy';
    
    res.status(dbHealth ? 200 : 503).json({
      status,
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      environment: env.NODE_ENV,
      database: dbHealth ? 'connected' : 'disconnected'
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Health check failed'
    });
  }
});

// API routes
app.use('/auth', authRoutes);
app.use('/user', userRoutes);
app.use('/media', mediaRoutes);
app.use('/analytics', analyticsRoutes);
app.use('/galleries', galleriesRoutes);
app.use('/stories', storiesRoutes);
app.use('/highlights', highlightsRoutes);
app.use('/marketing-tool', marketingToolRoutes);

// API info endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Crow\'s Eye Marketing Suite API',
    version: '1.0.0',
    description: 'REST API for social media management platform',
    documentation: '/docs',
    health: '/health',
    endpoints: {
      auth: '/auth',
      user: '/user',
      media: '/media',
      analytics: '/analytics',
      galleries: '/galleries',
      stories: '/stories',
      highlights: '/highlights',
      marketingTool: '/marketing-tool'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Route ${req.originalUrl} not found`
    }
  });
});

// Global error handler
app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Unhandled error:', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method,
    body: req.body,
    user: (req as any).user?.id
  });

  // Don't leak error details in production
  const message = isDevelopment ? error.message : 'Internal server error';
  const details = isDevelopment ? error.stack : undefined;

  res.status(error.status || 500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message,
      details
    }
  });
});

// Graceful shutdown
const gracefulShutdown = async (signal: string) => {
  logger.info(`Received ${signal}. Starting graceful shutdown...`);
  
  await disconnectDatabase();
  
  process.exit(0);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Start server
const startServer = async () => {
  try {
    // Try to connect to database (optional for demo)
    const dbConnected = await connectDatabase();
    
    // Start HTTP server regardless of database connection
    const server = app.listen(env.PORT, () => {
      logger.info(`🚀 Server running on port ${env.PORT}`);
      logger.info(`📚 API Documentation: http://localhost:${env.PORT}/docs`);
      logger.info(`❤️  Health Check: http://localhost:${env.PORT}/health`);
      logger.info(`🌍 Environment: ${env.NODE_ENV}`);
      
      if (!dbConnected) {
        logger.warn('⚠️  Running in demo mode - some features may not work without database');
        logger.info('💡 To enable full functionality, set up a PostgreSQL database');
      }
    });

    // Handle server shutdown
    const shutdownServer = () => {
      server.close(() => {
        logger.info('HTTP server closed');
      });
    };

    process.on('SIGTERM', shutdownServer);
    process.on('SIGINT', shutdownServer);

  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Initialize application
if (require.main === module) {
  startServer();
}

export default app; 