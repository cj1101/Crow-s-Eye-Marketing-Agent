import winston from 'winston';

const logFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(({ level, message, timestamp, stack }) => {
    return `${timestamp} [${level}]: ${stack || message}`;
  })
);

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { service: 'crow-eye-api' },
  transports: [
    new winston.transports.File({
      filename: process.env.LOG_FILE || 'logs/error.log',
      level: 'error',
    }),
    new winston.transports.File({
      filename: process.env.LOG_FILE || 'logs/combined.log',
    }),
  ],
});

// If we're not in production, log to the console as well
if (process.env.NODE_ENV !== 'production') {
  logger.add(
    new winston.transports.Console({
      format: consoleFormat,
    })
  );
}

// Create logs directory if it doesn't exist
import { mkdirSync } from 'fs';
import { dirname } from 'path';

try {
  const logDir = dirname(process.env.LOG_FILE || 'logs/app.log');
  mkdirSync(logDir, { recursive: true });
} catch (error) {
  // Directory might already exist
} 