DOMAIN = "oneminai"

API_BASE_URL = "https://api.1min.ai/api"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat-with-ai"
CONVERSATIONS_ENDPOINT = f"{API_BASE_URL}/conversations"

CHAT_TYPE = "UNIFY_CHAT_WITH_AI"

CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_WEB_SEARCH = "web_search"
CONF_NUM_OF_SITE = "num_of_site"
CONF_MAX_WORD = "max_word"
CONF_HISTORY_LIMIT = "history_limit"
CONF_SYSTEM_PROMPT = "system_prompt"
CONF_LOCAL_CONTROL = "local_control"
CONF_REQUEST_TIMEOUT = "request_timeout"

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_WEB_SEARCH = False
DEFAULT_NUM_OF_SITE = 3
DEFAULT_MAX_WORD = 1000
DEFAULT_HISTORY_LIMIT = 10
DEFAULT_LOCAL_CONTROL = True
DEFAULT_REQUEST_TIMEOUT = 60
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful voice assistant integrated into Home Assistant. "
    "Answer concisely and in the language of the user."
)

# Memory management
MAX_CONVERSATION_CACHE = 100
CONVERSATION_CACHE_TTL = 3600  # 1 hour

# Liste indicative de modèles courants exposés par 1min.ai
SUPPORTED_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "claude-3-5-sonnet-20240620",
    "claude-3-haiku-20240307",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "mistral-large-latest",
    "deepseek-chat",
]

SERVICE_ASK = "ask"
ATTR_PROMPT = "prompt"
ATTR_MODEL = "model"
ATTR_WEB_SEARCH = "web_search"
ATTR_IMAGES = "images"
ATTR_CONVERSATION_ID = "conversation_id"

TIMEOUT = DEFAULT_REQUEST_TIMEOUT