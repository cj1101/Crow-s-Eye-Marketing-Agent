# Breadsmith Marketing Tool - Meta App Review Documentation

## 1. Loading and Testing the App Externally

### Installation Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/breadsmith_marketing.git
   cd breadsmith_marketing
   ```

2. **Set Up Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initial Configuration**
   ```bash
   python initialize_app.py
   ```

4. **Configure Meta API Credentials**
   - Edit the `meta_credentials.json` file with your test credentials:
   ```json
   {
     "facebook_page_id": "YOUR_TEST_FB_PAGE_ID",
     "page_access_token": "YOUR_TEST_PAGE_ACCESS_TOKEN",
     "instagram_user_id": "YOUR_TEST_IG_USER_ID",
     "instagram_username": "YOUR_TEST_IG_USERNAME",
     "instagram_password": "YOUR_TEST_IG_PASSWORD",
     "use_mock_api_for_testing": false
   }
   ```

5. **Run the Application**
   ```bash
   python run.py
   ```

### Testing Credentials
For your review, we've created a test account with the following credentials that can be used to test all functionality:

- **Username**: breadsmith_test_reviewer@example.com
- **Password**: MetaReviewer2023!
- **Connected Instagram Business Account**: @breadsmith_test_account
- **Connected Facebook Page**: Breadsmith Test Page

## 2. Use Case Details & Step-by-Step Usage Instructions

### Primary Use Case: Social Media Marketing for Bakeries

Breadsmith Marketing Tool is designed to help bakeries and similar food businesses efficiently create and manage social media content, particularly for Instagram. The tool automates caption generation based on product images and facilitates scheduling posts for optimal engagement.

### Step-by-Step Usage Instructions:

#### A. Content Creation

1. **Launch the application** by running `python run.py`
2. **Select Media**
   - Click "Upload Media" button in the main window
   - Navigate to and select a photo of a bakery product
   - The image will appear in the preview panel

3. **Generate Caption**
   - Enter specific instructions in the text box (e.g., "Highlight the sourdough's texture and artisanal process")
   - Click "Generate Caption" button
   - Review the AI-generated caption in the text area
   - Edit the caption if needed

4. **Preview Post**
   - The combination of selected image and caption will be displayed in the preview panel
   - Make any final adjustments to the caption

5. **Post or Schedule**
   - Click "Post Now" to immediately publish to Instagram
   - Or click "Schedule" to set a future posting time

#### B. Content Scheduling

1. **Navigate to Schedule Tab**
   - Click on the "Schedule" tab in the main navigation

2. **Create New Schedule**
   - Click "Add Schedule" button
   - Select posting frequency (e.g., daily, weekly)
   - Choose specific days and times
   - Select content collection to use
   - Click "Save Schedule"

3. **Review Scheduled Content**
   - View calendar of upcoming posts
   - Edit or delete scheduled posts as needed

4. **Monitor Posting Status**
   - Check the "Status" tab to view successful posts and any errors
   - Receive notifications when scheduled posts are published

#### C. Content Library Management

1. **Access Library**
   - Click on "Library" tab in the main navigation

2. **Organize Content**
   - Create collections for different product categories
   - Tag and filter content
   - Search for specific items

3. **Batch Operations**
   - Select multiple items
   - Apply tags
   - Schedule multiple posts

## 3. Instagram Permissions Usage Documentation

Our application requires specific Instagram permissions to function properly. Below is a detailed explanation of how each permission is used in accordance with Meta's usage guidelines.

### instagram_basic Permission

**How it's used:**
- To retrieve basic information about the connected Instagram Business account
- To display account name and profile picture in the application interface
- To verify connectivity status with Instagram

**User flow demonstration:**
1. User connects their Instagram Business account
2. App displays account name and profile image in the account status section
3. App verifies the connection is valid before allowing posting operations

### instagram_content_publish Permission

**How it's used:**
- To publish photos and captions to the connected Instagram Business account
- To schedule posts for future publication
- To retrieve publishing status of posts

**User flow demonstration:**
1. User selects an image and caption in the application
2. User clicks "Post Now" or schedules the post for later
3. App uses the permission to submit the content to Instagram
4. App retrieves and displays the publishing status

### instagram_manage_comments Permission

**How it's used:**
- To retrieve comments on published posts
- To display engagement metrics in the application
- To respond to comments directly from the application (future feature)

**User flow demonstration:**
1. User navigates to the "Engagement" tab
2. App displays recent comments on published posts
3. User can view comment metrics and plan responses

### instagram_manage_insights Permission

**How it's used:**
- To retrieve performance metrics of published posts
- To display analytics dashboards in the application
- To generate performance reports for the user

**User flow demonstration:**
1. User navigates to the "Analytics" tab
2. App displays engagement metrics for recent posts
3. User can generate and export performance reports

### pages_read_engagement Permission

**How it's used:**
- To retrieve engagement metrics from the connected Facebook Page
- To provide cross-platform analytics
- To ensure proper account connectivity

**User flow demonstration:**
1. User connects both Instagram Business account and Facebook Page
2. App verifies proper connection between the accounts
3. App retrieves and displays cross-platform engagement metrics

### instagram_business_manage_messages Permission

**How it's used:**
- To receive and respond to Direct Messages (DMs) sent to the connected Instagram Business account.
- To read and reply to comments on the business's Instagram posts.
- To leverage the app's integrated "Knowledge Function" to provide automated or semi-automated responses based on a predefined knowledge base.
- To allow business users to manually review and send responses drafted by the knowledge function.

**User flow demonstration:**
1. **Connecting the Knowledge Function to Messaging:**
   - User navigates to Settings > Messaging & Knowledge Base.
   - User enables the "Automated Replies" feature for DMs and/or comments.
   - User selects the relevant knowledge base files to be used for generating responses.
2. **Receiving and Responding to DMs:**
   - The app receives an incoming DM in the "Inbox" tab.
   - If automated replies are enabled, the Knowledge Function drafts a response based on the DM content and the knowledge base.
   - The user can review the drafted DM response, edit if necessary, and approve it to be sent.
   - Alternatively, the user can manually type and send a response.
3. **Receiving and Responding to Comments:**
   - The app displays new comments under relevant posts in the "Engagement" or "Posts" tab.
   - If automated replies are enabled for comments, the Knowledge Function drafts a reply based on the comment content and knowledge base.
   - The user can review the drafted comment reply, edit, and approve it for posting.
   - Alternatively, the user can manually type and post a reply.
4. **Monitoring Automated Interactions:**
   - The app provides a log of all automated and manually approved responses sent via DMs or as comment replies.
   - Users can review the effectiveness of the Knowledge Function and update the knowledge base accordingly.

All permissions are used strictly for the purposes described above, with full transparency to the user about data access and usage. No user data is shared with third parties, and all analytics are displayed only to the authenticated account owner.

## Additional Documentation

### Privacy Policy
Our full privacy policy is available at: [https://www.breadsmithbakery.com/app-privacy-policy](https://www.breadsmithbakery.com/app-privacy-policy)

### Data Retention Policy
- User credentials are stored locally on the user's device only
- Content data (images, captions) are stored locally and in the user's connected accounts
- Analytics data is cached temporarily for display purposes only

### Support Contact
For any questions regarding our application's use of Instagram permissions, please contact:
- Email: support@breadsmithbakery.com
- Phone: (555) 123-4567 