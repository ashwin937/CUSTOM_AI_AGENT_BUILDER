# Instagram Integration Setup Guide

If you are having trouble finding the specific "Add Product" button for Instagram Graph API (Meta's UI changes frequently), follow this alternative method using the **Graph API Explorer**.

## Method: Using the Graph API Explorer (Recommended)

This method bypasses the confusing dashboard menus and directly requests the permissions you need.

### Prerequisites
1. You must have a **Facebook Page**.
2. You must have an **Instagram Professional Account** (Business or Creator).
3. Connect your Instagram account to your Facebook Page:
   - Go to your Facebook Page Settings -> Linked Accounts -> Instagram -> Connect.

### Step 1: Open the Graph API Explorer
1. Go to: [https://developers.facebook.com/tools/explorer/](https://developers.facebook.com/tools/explorer/)
2. Make sure you are logged into your developer account.

### Step 2: Configure the Token Request
On the right side of the screen:
1. **Meta App**: Select your app from the dropdown menu.
2. **User or Page**: Select "Get User Access Token".
3. A popup will appear. Select your user account.

### Step 3: Add Permissions
In the "Permissions" section (still on the right side), search for and add these EXACT permissions:
- `pages_show_list`
- `pages_read_engagement`
- `instagram_basic`
- `instagram_content_publish`

### Step 4: Generate the Token
1. Click **Generate Access Token**.
2. A popup will appear asking you to carry out the authorization.
3. **IMPORTANT**: Select the Facebook Page connected to your Instagram account.
4. **IMPORTANT**: Select the Instagram account you want to use.
5. Grant all requested permissions.

### Step 5: Get the Page ID and Token (Crucial Step)
The token you just got is a *User Token*. We need a *Page Token* or at least the *Instagram Account ID*.

1. In the query bar at the top (where it says `GET` and `v19.0` or similar), type:
   `me/accounts`
2. Click **Submit**.
3. In the response, find the entry for your Facebook Page.
4. Copy the `access_token` from that specific page entry. This is your **Page Access Token**.
5. Also, copy the `id` of the page.

### Step 6: Get Your Instagram Business Account ID
Now use the Page ID you just found.
1. In the query bar, type:
   `{PAGE_ID}?fields=instagram_business_account`
   (Replace `{PAGE_ID}` with the ID you copied in Step 5).
2. Click **Submit**.
3. The response will show:
   ```json
   {
     "instagram_business_account": {
       "id": "17841400000000000" // -> THIS IS YOUR INSTAGRAM_ACCOUNT_ID
     },
     "id": "..."
   }
   ```

### Step 7: Update Your .env File
Open your `.env` file in the project folder and paste the values:
```
INSTAGRAM_ACCESS_TOKEN=your_page_access_token_from_step_5
INSTAGRAM_ACCOUNT_ID=your_id_from_step_6
```

## Troubleshooting
- **"Application does not have permission for this action"**: Your specific app type (e.g., Business vs. Consumer) might restrict certain APIs. Ensure your app is in "Development" mode, not "Live".
- **Token Expiry**: The token from the explorer is short-lived (1 hour). For a permanent app, you would exchange it for a Long-Lived token, but for testing this agent, the short-lived one works fine.
