# Frappe Notifier

Push Notifications setup through Frappe Relay server

## Prerequisites

- [Google Cloud Authentication](https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to)
- Firebase project with Firebase Cloud Messaging (FCM) enabled
- Frappe Bench environment

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app frappe_notifier
```

## Setup Instructions

### 1. Firebase Service Account Configuration

1. Generate a `firebase_service_account.json` file from your Firebase project
2. Place the `firebase_service_account.json` file in your bench directory
3. Run the initialization script from the bench directory:

```bash
source ./apps/frappe_notifier/init.sh
```

### 2. Common Site Configuration

Add the push relay server URL to your `common_site_config.json`:

```json
{
  "push_relay_server_url": "https://your-site-domain.com"
}
```

**Example:**
```json
{
  "push_relay_server_url": "https://visaguy.erpcode.tridz.in"
}
```

### 3. Site Configuration

Add the hostname to the domains array in your `site_config.json`:

```json
{
  "domains": [
    "your-site-domain.com"
  ],
  "hostname": "your-site-domain.com"
}
```

**Example:**
```json
{
  "domains": [
    "visaguy.erpcode.tridz.in"
  ],
  "hostname": "visaguy.erpcode.tridz.in"
}
```

### 4. Push Notification Settings Verification

After installation, verify the "Push Notification Settings":

1. Navigate to **Setup > Push Notification Settings**
2. Ensure "Enable Push Notifications" is checked
3. Verify that API Key and API Secret are generated
4. If API Key/Secret are missing:
   - Check if "Notification Manager" user exists
   - If not, create the "Notification Manager" user
   - Generate API key and secret for this user

### 5. Firebase Configuration in Frappe Notifier Settings

Add your Firebase project values to the Frappe Notifier Settings doctype:

**Example Configuration:**
- **Project ID:** `your-firebase-project-id`
- **Vapid Public Key:** `your-vapid-public-key`
- **Firebase Config:**
```json
{
    "apiKey": "your-api-key",
    "authDomain": "your-project.firebaseapp.com",
    "projectId": "your-project-id",
    "storageBucket": "your-project.firebasestorage.app",
    "messagingSenderId": "your-sender-id",
    "appId": "your-app-id",
    "measurementId": "your-measurement-id"
}
```

**Note:** Replace the example values with your actual Firebase project configuration. The values shown above are masked for security purposes.

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/frappe_notifier
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

## License

MIT
