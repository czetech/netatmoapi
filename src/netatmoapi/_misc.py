from logging import getLogger

_module = __name__.split(".")[0]

logger = getLogger(_module)

# Default values
API_URL = "https://api.netatmo.com"
CLIENT_ID = "na_client_android_magellan"
CLIENT_SECRET = "a6e15c52b06364b3251b2c5ae3dd8521"
SCOPE = "all_scopes"
WEBSOCKET_URL = "https://app.netatmo.net/ws/"
WEBSOCKET_APP_TYPES = ("app_magellan", "app_camera")
