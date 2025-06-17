# GCP Database Configuration Fix Guide

## 🎯 Overview

This guide addresses the critical database configuration issues in your GCP backend deployment:

1. **SQLite Path Issue**: Fixed ephemeral `/tmp` directory usage
2. **Database Driver Mismatch**: Corrected SQLite URL format
3. **Missing Database Initialization**: Added automatic database setup
4. **Production Database Options**: Provided both SQLite and PostgreSQL solutions

---

## 🔧 Issues Fixed

### ❌ **Previous Issues**
- Database URL used `sqlite://` instead of `sqlite+aiosqlite://`
- Database file stored in `/tmp` (ephemeral in GCP App Engine)
- No database initialization on first deployment
- Missing environment variables for production

### ✅ **Fixed Configuration**
- Corrected database URL format
- Moved database to persistent `/opt/app/data/` directory
- Added automatic database initialization
- Comprehensive environment variable setup

---

## 🚀 Deployment Options

### Option 1: SQLite (Recommended for Small-Medium Applications)

**Pros:**
- Simple setup
- Cost-effective
- Good for development and small production
- Zero additional Google Cloud costs

**Cons:**
- Limited scalability
- Single connection limitations
- File-based storage

**Configuration:**
```yaml
# app.yaml
env_variables:
  DATABASE_URL: "sqlite+aiosqlite:///opt/app/data/crow_eye_production.db"
  INITIALIZE_DB: "true"
```

### Option 2: PostgreSQL with Cloud SQL (Recommended for Large-Scale)

**Pros:**
- Highly scalable
- Production-grade reliability
- Automatic backups
- Multi-region support

**Cons:**
- Additional costs (~$25-50/month minimum)
- More complex setup
- Requires Cloud SQL instance

**Configuration:**
```yaml
# app.yaml
env_variables:
  DATABASE_URL: "postgresql+asyncpg://username:password@/dbname?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME"
  INITIALIZE_DB: "true"
```

---

## 📁 Files Modified/Created

### 🔄 **Modified Files**
1. **`app.yaml`**
   - Fixed DATABASE_URL format
   - Changed path from `/tmp` to `/opt/app/data`
   - Added INITIALIZE_DB flag

2. **`deploy_main.py`**
   - Added database initialization on startup
   - Improved health checks with database status
   - Better error handling and logging

3. **`requirements-production.txt`**
   - Added PostgreSQL drivers (`asyncpg`, `psycopg2-binary`)
   - Added Cloud SQL connector packages
   - Optimized for GCP deployment

### 📄 **New Files Created**
1. **`initialize_gcp_db.py`**
   - Automatic database initialization
   - Creates database file and directory
   - Initializes all tables

2. **`setup_cloud_sql.py`**
   - Cloud SQL PostgreSQL setup script
   - Connection testing
   - Database initialization for PostgreSQL

3. **`env_gcp_template.txt`**
   - Comprehensive environment configuration template
   - Both SQLite and PostgreSQL options
   - Production-ready settings

---

## 🎯 Quick Deployment Steps

### SQLite Option (Simple)

1. **Verify Configuration**
   ```bash
   # Check app.yaml has correct DATABASE_URL
   cat app.yaml | grep DATABASE_URL
   ```

2. **Deploy to GCP**
   ```bash
   gcloud app deploy app.yaml
   ```

3. **Test Deployment**
   ```bash
   curl https://your-app-url.uc.r.appspot.com/health
   ```

### PostgreSQL Option (Advanced)

1. **Create Cloud SQL Instance**
   ```bash
   gcloud sql instances create crow-eye-db \
     --database-version=POSTGRES_14 \
     --region=us-central1 \
     --tier=db-f1-micro
   ```

2. **Set Environment Variables**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export POSTGRES_PASSWORD=your-secure-password
   export CLOUD_SQL_REGION=us-central1
   export CLOUD_SQL_INSTANCE=crow-eye-db
   ```

3. **Run Setup Script**
   ```bash
   python setup_cloud_sql.py
   ```

4. **Update app.yaml with PostgreSQL URL**

5. **Deploy**
   ```bash
   gcloud app deploy app.yaml
   ```

---

## 🔍 Troubleshooting

### Common Issues

#### Database File Not Found
**Symptom:** `no such file or directory` errors
**Solution:** Ensure `INITIALIZE_DB=true` in app.yaml

#### Connection Refused
**Symptom:** Database connection failures
**Solution:** Check database URL format and file permissions

#### Import Errors
**Symptom:** Module import failures
**Solution:** Verify all models are imported in `initialize_gcp_db.py`

### Health Check Commands

```bash
# Check deployment status
gcloud app describe

# View logs
gcloud app logs tail -s default

# Test health endpoint
curl https://your-app-url.uc.r.appspot.com/health

# Test API endpoints
curl https://your-app-url.uc.r.appspot.com/api/v1/health
```

---

## 📊 Database Performance

### SQLite Performance Tips
- Use WAL mode for better concurrency
- Regular VACUUM operations
- Monitor file size growth

### PostgreSQL Performance Tips
- Use connection pooling
- Monitor Cloud SQL metrics
- Configure appropriate instance size

---

## 🔒 Security Considerations

### SQLite Security
- File-level permissions in GCP App Engine
- No network exposure
- Automatic encryption at rest

### PostgreSQL Security
- Private IP connections
- SSL/TLS encryption
- IAM-based authentication (recommended)
- Automatic backups

---

## 💰 Cost Analysis

### SQLite Costs
- **Database:** $0 (file-based)
- **Storage:** Standard App Engine storage costs
- **Total:** ~$5-20/month (depending on usage)

### PostgreSQL Costs
- **Cloud SQL:** $25-50/month (minimum)
- **Storage:** Additional storage costs
- **Network:** Egress charges
- **Total:** ~$40-100/month (depending on instance size)

---

## 🎉 Success Indicators

When deployment is successful, you should see:

1. **Health Check Returns 200**
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "service": "crow-eye-api"
   }
   ```

2. **Database Tables Created**
   - Check logs for "Database tables created successfully"

3. **API Endpoints Working**
   - `/docs` shows API documentation
   - `/api/v1/health` returns healthy status

---

## 📞 Support

If you encounter issues:

1. **Check Logs:** `gcloud app logs tail -s default`
2. **Verify Environment:** Ensure all required env vars are set
3. **Test Locally:** Run initialization scripts locally first
4. **Database Status:** Check database file/instance status

The configuration is now production-ready with proper error handling, initialization, and monitoring! 🚀 