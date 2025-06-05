// Development environment setup
require('dotenv').config();

// Set required environment variables for development
process.env.DATABASE_URL = process.env.DATABASE_URL || "file:./dev.db";
process.env.JWT_SECRET = process.env.JWT_SECRET || "dev-super-secret-jwt-key-for-development-only-change-in-production";
process.env.JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || "dev-super-secret-refresh-jwt-key-for-development-only-change-in-production";
process.env.JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || "24h";
process.env.JWT_REFRESH_EXPIRES_IN = process.env.JWT_REFRESH_EXPIRES_IN || "30d";
process.env.PORT = process.env.PORT || "3001";
process.env.NODE_ENV = process.env.NODE_ENV || "development";
process.env.CORS_ORIGINS = process.env.CORS_ORIGINS || "http://localhost:3000,https://crows-eye-website.web.app";

console.log('✅ Development environment configured');
console.log('🔧 Using SQLite database for development');
console.log('🔧 Starting server on port', process.env.PORT); 