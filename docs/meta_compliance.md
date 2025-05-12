# Compliance with Meta Platform Policies

This document outlines how the Breadsmith Marketing Tool complies with Meta Platform Policies, specifically related to the use of Instagram Graph API and Facebook Graph API. The document is intended for Meta App Review team members and technical stakeholders.

## API Usage and Permission Justification

### Permission: instagram_basic

**Business Justification:**
The `instagram_basic` permission is essential for our application to retrieve basic information about the connected Instagram Business account, which enables proper account verification and user experience personalization.

**Technical Implementation:**
- We retrieve basic profile information (username, profile picture) only at login and when explicitly refreshed by the user
- Implementation follows the principle of least privilege, using only necessary endpoints
- All data is cached locally to minimize API calls

**Endpoints Used:**
```
GET /{ig-user-id}
GET /{ig-user-id}/media
```

**Code Reference:**
The implementation can be found in `src/handlers/media_handler.py` lines 470-509, which handles loading and validating Meta credentials.

### Permission: instagram_content_publish

**Business Justification:**
The `instagram_content_publish` permission is core to our application's primary functionality: allowing bakeries to publish content to their Instagram accounts, either immediately or on a schedule.

**Technical Implementation:**
- We implement rate limiting to prevent API abuse
- All uploads are user-initiated or approved through the scheduling interface
- Content is validated against Instagram's guidelines before submission
- We handle and display all API errors appropriately to users

**Endpoints Used:**
```
POST /{ig-user-id}/media
POST /{ig-user-id}/media_publish
GET /{ig-container-id}?fields=status_code
```

**Error Handling:**
- We check container status before publishing
- We implement exponential backoff for retries
- Users are notified of failures with actionable error messages

### Permission: instagram_manage_comments

**Business Justification:**
The `instagram_manage_comments` permission allows our users to monitor engagement with their content directly within our app, enabling better community management and response strategies.

**Technical Implementation:**
- Comments are retrieved only for published posts
- Comment data is refreshed only when requested by the user
- We implement pagination to efficiently retrieve larger comment sets
- All comment data is displayed in a read-only format (responding to comments is a planned future feature)

**Endpoints Used:**
```
GET /{media-id}/comments
GET /{comment-id}
```

**Data Protection:**
- Comment data is not stored permanently unless explicitly saved by the user
- Comment metrics are anonymized when used in analytics

### Permission: instagram_manage_insights

**Business Justification:**
The `instagram_manage_insights` permission is critical for our analytics dashboard, allowing bakeries to understand the performance of their content and optimize their social media strategy.

**Technical Implementation:**
- Insights are retrieved with appropriate date ranges to minimize data transfer
- Data is cached appropriately with time-to-live values
- Aggregated metrics are calculated client-side when possible
- We respect all rate limits and implement queuing when necessary

**Endpoints Used:**
```
GET /{ig-user-id}/insights
GET /{media-id}/insights
```

**Performance Considerations:**
- Batch requests are used when retrieving insights for multiple posts
- Insights are loaded asynchronously to prevent UI blocking
- Date ranges are limited to reasonable periods (max 30 days for most metrics)

### Permission: pages_read_engagement

**Business Justification:**
The `pages_read_engagement` permission enables cross-platform analytics between Instagram and Facebook, providing users with a holistic view of their social media presence.

**Technical Implementation:**
- We verify proper connection between Instagram and Facebook accounts
- Engagement data is used only for display within the application
- Data is refreshed only when explicitly requested by the user

**Endpoints Used:**
```
GET /{page-id}/insights
GET /{page-id}/posts
```

**User Privacy:**
- All engagement data is visible only to the authenticated business owner
- No individual user data from engagements is extracted or stored

### Permission: instagram_business_manage_messages

**Business Justification:**
This permission allows our application to manage direct messages and comments on behalf of the business. It integrates with our "Knowledge Function" (powered by local knowledge base files) to assist users in responding to customer inquiries efficiently, thereby enhancing customer engagement and support capabilities for bakeries using our tool.

**Technical Implementation:**
- **Receiving Messages/Comments:** The application will use webhooks (if available and configured by the user) or periodic polling to fetch new DMs and comments.
- **Knowledge Function Integration:** Incoming messages/comments are processed by the `KnowledgeSimulatorDialog` (from `knowledge_simulator.py`) which queries local files in the `knowledge_base/` directory to find relevant information and draft responses.
- **Response Moderation:** All AI-drafted responses are presented to the user for review, editing, and manual approval before being sent. No automated responses are sent without explicit user action for each message.
- **Manual Responses:** Users can also craft and send responses manually without using the knowledge function.
- **Data Handling:** Message content is processed for generating responses but not stored long-term unless explicitly saved by the user in a local audit log (a planned feature). No message content is used for training AI models outside of the user's local knowledge base context.

**Endpoints Used (Conceptual - actual endpoints depend on specific Instagram API capabilities for messaging bots/integrations via the Graph API):
**
```
# For DMs (Instagram Direct Messaging API)
GET /{ig-user-id}/conversations
GET /{conversation-id}/messages
POST /{conversation-id}/messages

# For Comments
GET /{media-id}/comments
POST /{media-id}/comments  (to reply to a comment, if distinct from replying to a top-level media comment)
POST /{comment-id}/replies (to reply to a specific comment)
```

**Error Handling & Data Protection:**
- Standard API error handling (retries, user notifications) will be implemented.
- Sensitive message data is handled locally and only transmitted to Meta APIs for sending approved responses.
- Access to messaging features will be strictly permission-based within the app.
- Users will be clearly informed about how their knowledge base files are used to generate response drafts.

## Compliance with Platform Policies

### Data Use Policy Compliance

1. **User Consent**
   - We clearly inform users about data collection and use
   - Our privacy policy explicitly states how Meta data is used
   - Users must opt-in to data collection for analytics features

2. **Data Retention**
   - Meta API data is not stored longer than necessary for the feature
   - Users can delete data at any time through our application
   - We implement automatic data purging for inactive accounts

3. **Third-Party Sharing**
   - We do not share data retrieved from Meta APIs with any third parties
   - Analytics are for the user's eyes only
   - No data mining or aggregation across accounts is performed

### Technical Security Measures

1. **Authentication Security**
   - We use secure OAuth 2.0 flows for authentication
   - Access tokens are stored securely using industry-standard encryption
   - Tokens are never exposed in client-side code or logs

2. **Data Transmission**
   - All API requests use HTTPS
   - Data is encrypted in transit
   - API keys and secrets are never included in client-side code

3. **Rate Limiting & Efficiency**
   - We implement client-side rate limiting to prevent API abuse
   - Batch requests are used when appropriate
   - Exponential backoff is implemented for API retries

## Quality Assurance & Testing

### Testing Protocol

1. **API Integration Tests**
   - Automated tests verify correct API usage
   - Edge cases and error conditions are tested
   - Integration tests run before each release

2. **Permission Verification**
   - Each feature is tested with minimal required permissions
   - Tests confirm app degrades gracefully when permissions are missing
   - All error messages are user-friendly and actionable

3. **Data Validation**
   - Input validation occurs before API calls
   - Output validation ensures data integrity
   - Corrupt or unexpected data is handled appropriately

### Monitoring & Maintenance

1. **API Changes**
   - We actively monitor Meta Platform changelog and developer newsletters
   - Updates are implemented promptly for deprecated endpoints or parameters
   - Users are notified of significant API changes that affect functionality

2. **Error Reporting**
   - Detailed error logging for API interactions
   - Automatic alerting for unusual error rates
   - Regular review of error patterns to improve reliability

3. **Performance Monitoring**
   - API call volume and patterns are monitored
   - Performance optimizations are regularly implemented
   - Caching strategies are adjusted based on usage patterns

## Documentation & Support

1. **User Documentation**
   - Clear explanations of Meta-connected features
   - Step-by-step guides for authentication and setup
   - Troubleshooting information for common issues

2. **Developer Documentation**
   - Internal documentation of all API integrations
   - Consistent code patterns for API calls
   - Clear separation of API logic from business logic

3. **Support Channels**
   - Dedicated support for Meta-related connection issues
   - Clear error messages with suggested actions
   - Regular updates about Meta platform changes that affect the app

## Commitment to Policy Compliance

We are committed to maintaining strict compliance with Meta Platform Policies. Our development team regularly reviews updated policies and guidelines, and we proactively adjust our application to ensure continued compliance.

For any questions regarding our compliance with Meta Platform Policies, please contact our compliance team at compliance@breadsmithbakery.com or call (555) 123-4567. 