"""Constants for the TickTick Integration integration."""

DOMAIN = "ticktick"

# === Authentication Configuration ===
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# === Options Configuration === #
CONF_COMPLETED_TASKS_DAYS = "completed_tasks_days"
DEFAULT_COMPLETED_TASKS_DAYS = 7

# === Per-Project Configuration === #
CONF_PROJECT_CONFIGS = "project_configs"
CONF_PROJECT_ENABLED = "enabled"
CONF_PROJECT_COMPLETED_ENABLED = "completed_enabled"
CONF_PROJECT_COMPLETED_DAYS = "completed_days"

# === Legacy OAuth2 constants (for migration compatibility) === #
# These are kept for detecting old OAuth2 config entries
LEGACY_OAUTH2_AUTHORIZE = "https://ticktick.com/oauth/authorize"
LEGACY_OAUTH2_TOKEN = "https://ticktick.com/oauth/token"
