# 🐦‍⬛ Crow's Eye Subscription System Integration Guide

This guide explains how to integrate the subscription-based access control system into your Crow's Eye Marketing Platform.

## 📋 Overview

The subscription system provides:
- **User Authentication**: Login/registration with secure password hashing
- **Subscription Tiers**: Free and Pro tiers with different feature sets
- **Feature Access Control**: Automatic enforcement of tier-based feature access
- **Usage Limits**: Monthly quotas for posts, videos, AI requests, and storage
- **Upgrade Flows**: Seamless upgrade dialogs and payment integration points

## 🏗️ Architecture

### Core Components

1. **User Model** (`src/models/user.py`)
   - User account management
   - Subscription information
   - Usage statistics tracking

2. **Access Control** (`src/features/subscription/access_control.py`)
   - Feature access enforcement
   - Usage limit checking
   - Subscription tier definitions

3. **UI Components**
   - `UserAuthDialog`: Login/registration interface
   - `SubscriptionStatusWidget`: Real-time status display
   - Utility functions for seamless integration

## 🚀 Quick Start

### 1. Test the System

Run the test script to see the subscription system in action:

```bash
python test_subscription_system.py
```

This demonstrates:
- User registration and login
- Feature access control
- Usage limit enforcement
- Upgrade flows

### 2. Basic Integration

Add the subscription status widget to your main window:

```python
from src.ui.widgets.subscription_status_widget import SubscriptionStatusWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Add subscription status widget to your layout
        self.subscription_widget = SubscriptionStatusWidget()
        # Add to your layout...
```

### 3. Protect Features

Use decorators to protect features and enforce usage limits:

```python
from src.utils.subscription_utils import requires_feature_qt, requires_usage_qt
from src.features.subscription.access_control import Feature

class VideoGenerator(QWidget):
    
    @requires_feature_qt(Feature.VEO_VIDEO_GENERATOR)
    @requires_usage_qt('ai_content_credits_per_month', 1)
    def generate_video(self):
        """Generate a video (Pro feature, uses AI credits)."""
        # Your video generation code here
        pass
```

## 📊 Subscription Tiers

### Free Plan ($0/month)
- **Linked Social Accounts**: 1
- **Users**: 1
- **AI Credits**: 25 per month
- **Scheduled Posts**: 10 per month
- **Media Storage**: 500MB
- **Features**: Basic Content Tools (Media Library, Basic Image Editing), Basic Analytics Reports, Community Support

### Creator Plan ($19/month)
- **Linked Social Accounts**: 3
- **Users**: 1
- **AI Credits**: 150 per month
- **Scheduled Posts**: 100 per month
- **Media Storage**: 5GB
- **Features**: All Free features, plus Smart AI Gallery Generator, Advanced Post Formatting Tools, Basic Video Processing Tools, Email Support
- **AI Credit Packs**: Available for purchase (50 credits, 100 credits)

### Pro Plan ($50/month)
- **Linked Social Accounts**: 10
- **Users**: Up to 3
- **AI Credits**: 750 per month
- **Scheduled Posts**: Unlimited
- **Media Storage**: 50GB
- **Features**: All Creator features, plus Full Video Editing Suite, VEO AI Video Generation, AI Highlight Reels, AI Story Assistant, Bulk Operations, Audio Importer, Advanced Analytics & Reporting, Team Collaboration Tools, Priority Email Support
- **AI Credit Packs**: Available for purchase (100 credits, 250 credits)

### Business Plan (Custom Pricing)
- **Linked Social Accounts**: Custom/High Volume
- **Users**: Custom/More Users included
- **AI Credits**: Custom/High Volume
- **Scheduled Posts**: Unlimited
- **Media Storage**: Custom/High Volume
- **Features**: All Pro features, plus Advanced Team Collaboration Features, Custom Analytics & Reporting Dashboards, Custom Branding Options, API Access, Dedicated Account Manager & Premium Support

## 🔧 Integration Examples

### 1. Protecting a Button Click

```python
from src.utils.subscription_utils import check_feature_access_with_dialog

def on_analytics_button_clicked(self):
    if check_feature_access_with_dialog(Feature.PERFORMANCE_ANALYTICS, self):
        self.show_analytics_dashboard()
```

### 2. Checking Usage Before Action

```python
from src.utils.subscription_utils import check_usage_limit_with_dialog
from src.models.user import user_manager

def create_ai_content(self):
    if check_usage_limit_with_dialog('ai_content_credits_per_month', 1, self):
        # Create the AI content
        self.do_create_ai_content()
        # Usage is automatically incremented by the decorator

def schedule_post(self):
    if check_usage_limit_with_dialog('scheduled_posts_per_month', 1, self):
        # Schedule the post
        self.do_schedule_post()
        # Usage is automatically incremented by the decorator
```

### 3. Visual Feature Indicators

```python
from src.features.subscription.access_control import access_control, Feature

def update_button_style(self, button, feature):
    if access_control.has_feature_access(feature):
        button.setStyleSheet("/* Normal style */")
        button.setEnabled(True)
    else:
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFD700, stop:1 #FFA500);
                color: #8B4513;
                border: 2px solid #DAA520;
            }
        """)
        button.setText(button.text() + " (Pro)")
```

### 4. Usage Progress Indicators

```python
from src.features.subscription.access_control import access_control

def update_usage_display(self):
    usage_info = access_control.get_usage_info()
    if usage_info:
        accounts_data = usage_info["usage"]["social_accounts"]
        self.accounts_progress.setMaximum(accounts_data["limit"])
        self.accounts_progress.setValue(accounts_data["current"])
```

## 🎨 UI Integration Patterns

### 1. Feature Cards with Pro Badges

```python
class FeatureCard(QFrame):
    def __init__(self, title, description, feature, is_pro=False):
        super().__init__()
        # ... setup layout ...
        
        if is_pro:
            pro_badge = QLabel("PRO")
            pro_badge.setStyleSheet("""
                QLabel {
                    background-color: #FFD700;
                    color: #8B4513;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            layout.addWidget(pro_badge)
```

### 2. Upgrade Prompts

```python
from src.utils.subscription_utils import show_upgrade_dialog

def on_pro_feature_clicked(self):
    if not access_control.has_feature_access(Feature.VEO_VIDEO_GENERATOR):
        show_upgrade_dialog(self, "Video Generation")
```

### 3. Usage Warnings

```python
from src.utils.subscription_utils import create_usage_warning_style

def update_usage_warning(self, percentage):
    style = create_usage_warning_style(percentage)
    self.usage_label.setStyleSheet(style)
    
    if percentage >= 90:
        self.usage_label.setText("⚠️ Almost at limit!")
```

## 🔐 Security Considerations

### Password Hashing
The system uses SHA-256 for demo purposes. For production:

```python
import bcrypt

# In user creation
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# In authentication
bcrypt.checkpw(password.encode('utf-8'), stored_hash)
```

### Data Storage
- User data is stored in JSON files in the `data/` directory
- Passwords are hashed before storage
- Session data is cleared on logout

## 💳 Payment Integration

The system includes placeholder payment integration. To add real payments:

### 1. Stripe Integration Example

```python
import stripe

def process_upgrade_payment(self, payment_method_id, tier, amount):
    try:
        stripe.PaymentIntent.create(
            amount=amount,  # Amount in cents (e.g., 1900 for $19.00)
            currency='usd',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
        )
        
        # On success, upgrade user to specified tier
        user_manager.upgrade_to_tier(tier, "stripe")
        return True
    except stripe.error.StripeError as e:
        return False
```

### 2. Webhook Handling

```python
def handle_stripe_webhook(self, event):
    if event['type'] == 'payment_intent.succeeded':
        # Upgrade user to Pro
        user_id = event['data']['object']['metadata']['user_id']
        # ... upgrade logic ...
    elif event['type'] == 'invoice.payment_failed':
        # Downgrade user or send notification
        pass
```

## 📱 Mobile/Web Considerations

### Responsive Design
The subscription widgets are designed to be responsive:

```python
def setup_responsive_layout(self):
    if self.width() < 600:  # Mobile view
        self.subscription_widget.setMaximumHeight(120)
    else:  # Desktop view
        self.subscription_widget.setMaximumHeight(180)
```

### API Integration
For web/mobile apps, expose subscription data via API:

```python
@app.route('/api/user/subscription')
def get_subscription_info():
    user = get_current_user()
    return jsonify(access_control.get_usage_info())
```

## 🧪 Testing

### Unit Tests

```python
import unittest
from src.models.user import UserManager, SubscriptionTier

class TestSubscriptionSystem(unittest.TestCase):
    
    def setUp(self):
        self.user_manager = UserManager("test_data")
    
    def test_user_creation(self):
        user = self.user_manager.create_user("test@example.com", "testuser", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.subscription.tier, SubscriptionTier.FREE)
    
    def test_feature_access(self):
        # Test free user access
        self.assertFalse(access_control.has_feature_access(Feature.VEO_VIDEO_GENERATOR))
        
        # Upgrade and test
        self.user_manager.upgrade_to_pro()
        self.assertTrue(access_control.has_feature_access(Feature.VEO_VIDEO_GENERATOR))
```

### Integration Tests

Run the test script to verify end-to-end functionality:

```bash
python test_subscription_system.py
```

## 🔄 Migration Guide

### From Existing App

1. **Add User Authentication**
   ```python
   # Replace existing auth with subscription auth
   from src.models.user import user_manager
   
   # Check if user is logged in
   if user_manager.is_authenticated():
       # User is logged in
   ```

2. **Protect Existing Features**
   ```python
   # Add decorators to existing methods
   @requires_feature_qt(Feature.PERFORMANCE_ANALYTICS)
   def show_analytics(self):
       # Existing analytics code
   ```

3. **Add Usage Tracking**
   ```python
   # Add usage tracking to existing actions
   @requires_usage_qt('posts', 1)
   def create_post(self):
       # Existing post creation code
   ```

## 📈 Analytics and Monitoring

### Usage Analytics

```python
def get_usage_analytics(self):
    """Get usage analytics for admin dashboard."""
    users = self.user_manager._load_users()
    
    analytics = {
        'total_users': len(users),
        'pro_users': sum(1 for u in users.values() if u.get('subscription', {}).get('tier') == 'pro'),
        'free_users': sum(1 for u in users.values() if u.get('subscription', {}).get('tier') == 'free'),
        'monthly_revenue': len([u for u in users.values() if u.get('subscription', {}).get('tier') == 'pro']) * 5
    }
    
    return analytics
```

### Feature Usage Tracking

```python
def track_feature_usage(feature_name):
    """Track which features are being used most."""
    # Log feature usage for analytics
    logger.info(f"Feature used: {feature_name}")
```

## 🚀 Deployment

### Environment Variables

```bash
# Production settings
CROW_EYE_ENV=production
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=postgresql://...
```

### Database Migration

For production, migrate from JSON to database:

```python
def migrate_to_database(self):
    """Migrate user data from JSON to database."""
    users = self._load_users()
    for user_id, user_data in users.items():
        # Insert into database
        db.users.insert(user_data)
```

## 🎯 Best Practices

1. **Always Check Access**: Use decorators or utility functions consistently
2. **Graceful Degradation**: Show upgrade prompts instead of hiding features
3. **Clear Communication**: Make subscription benefits obvious
4. **Usage Feedback**: Show real-time usage information
5. **Smooth Upgrades**: Make upgrading as frictionless as possible

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all paths are correct in your project structure
2. **Permission Denied**: Check that user is authenticated before checking features
3. **Usage Not Updating**: Ensure decorators are applied correctly
4. **UI Not Refreshing**: Call `refresh()` on subscription widgets after changes

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

For questions about the subscription system:
1. Check the test script for examples
2. Review the utility functions in `subscription_utils.py`
3. Look at the video tools integration example

---

**Built with ❤️ for creators who want to survive and thrive in the digital landscape.** 