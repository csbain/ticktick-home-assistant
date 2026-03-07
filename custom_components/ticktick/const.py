"""Constants for the TickTick Integration integration."""

DOMAIN = "ticktick"

# === Authentication Configuration ===
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_V1_CLIENT_ID = "v1_client_id"
CONF_V1_CLIENT_SECRET = "v1_client_secret"
CONF_V1_CLIENT_ID = "v1_client_id"
CONF_V1_CLIENT_SECRET = "v1_client_secret"

# === Options Configuration === #
CONF_COMPLETED_TASKS_DAYS = "completed_tasks_days"
DEFAULT_COMPLETED_TASKS_DAYS = 7

# === Legacy OAuth2 constants (for migration compatibility) === #
# These are kept for detecting old OAuth2 config entries
LEGACY_OAUTH2_AUTHORIZE = "https://ticktick.com/oauth/authorize"
LEGACY_OAUTH2_TOKEN = "https://ticktick.com/oauth/token"
