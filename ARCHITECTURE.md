# Architecture - 1min.ai Home Assistant Integration

## Structure du projet

```
oneminai/
├── __init__.py              # Setup de l'intégration & service handler
├── api.py                   # Client async pour 1min.ai API
├── conversation.py          # Entité agent de conversation (Assist)
├── config_flow.py           # Configuration UI (HACS)
├── const.py                 # Constantes & défauts
├── manifest.json            # Métadonnées intégration
├── services.yaml            # Définition du service oneminai.ask
├── strings.json             # Traductions (anglais)
├── translations/
│   └── fr.json              # Traductions français
├── icon.png                 # Icône (HACS)
├── requirements.txt         # Dépendances (vide)
├── README.md                # Documentation utilisateur
├── CHANGELOG.md             # Historique versions
├── LICENSE                  # MIT License
└── .gitignore               # Git ignore
```

## Flux d'exécution

### 1. Setup initial (`__init__.py`)

```python
async_setup_entry(hass, entry)
    ├─ Crée OneMinAIClient avec clé API
    ├─ Valide la clé API (appel ping)
    ├─ Enregistre l'entité de conversation
    └─ Enregistre le service oneminai.ask
```

### 2. Traitement d'une requête (conversation.py)

```
User: "Allume le salon"
    ↓
OneMinAIConversationEntity.async_process()
    ├─ CONF_LOCAL_CONTROL=true?
    │  ├─ Oui → _async_try_local_intents()
    │  │        ├─ Utilise default_agent (Assist local)
    │  │        ├─ Si MATCH → retourner résultat local
    │  │        └─ Si NO_MATCH → fallthrough
    │  └─ Non → continuer
    │
    ├─ _async_process_llm()
    │  ├─ Nettoyage cache (_cleanup_conversation_cache)
    │  ├─ Réutiliser ou créer conversation distante
    │  ├─ Ajouter system prompt si première requête
    │  ├─ Appel OneMinAIClient.chat()
    │  └─ Retourner réponse
    ↓
Response -> User
```

### 3. Communication API (api.py)

```
OneMinAIClient.chat(prompt, model, ...)
    ├─ Valide les paramètres
    ├─ POST to https://api.1min.ai/api/chat-with-ai
    │  ├─ Headers: API-KEY, Content-Type
    │  ├─ Timeout: TIMEOUT (configurable)
    │  ├─ Payload: model, promptObject, settings
    │  └─ Retry sur timeout/erreur
    ├─ Parse response (_extract_answer)
    │  ├─ Cherche aiRecord.aiRecordDetail.resultObject
    │  ├─ Fallback sur plusieurs clés (text, content, answer)
    │  └─ Retourner string ou raise OneMinAIError
    ↓
Returns: str (réponse IA)
```

## Gestion mémoire

### Cache de conversations

```python
_remote_conversations = {
    "conv_id_1": (remote_uuid_1, timestamp_1),
    "conv_id_2": (remote_uuid_2, timestamp_2),
    ...
}
```

**Limite**: MAX_CONVERSATION_CACHE = 100
**TTL**: CONVERSATION_CACHE_TTL = 3600 secondes

**Nettoyage** (_cleanup_conversation_cache):
1. Supprimer les conversations expirées (TTL)
2. Supprimer les plus anciennes si dépassement de limite

Appelé automatiquement à chaque nouveau message.

## Configuration

### Config Entry (data)
```json
{
  "api_key": "sk-..."  // Clé API 1min.ai
}
```

### Options (options)
```json
{
  "model": "gpt-4o-mini",
  "system_prompt": "You are...",
  "local_control": true,
  "web_search": false,
  "num_of_site": 3,
  "max_word": 1000,
  "history_limit": 10,
  "request_timeout": 60
}
```

## Service: oneminai.ask

**Endpoint**: `oneminai.ask`

**Paramètres**:
- `prompt` (requis): Question/instruction
- `model` (optionnel): Modèle (défaut: config)
- `web_search` (optionnel): Activer recherche web
- `images` (optionnel): Liste d'URLs d'images
- `conversation_id` (optionnel): UUID pour contexte

**Retour**:
```json
{
  "response": "Réponse texte de l'IA"
}
```

## Gestion d'erreurs

| Erreur | Gestion |
|--------|---------|
| `OneMinAIAuthError` | Lève `ConfigEntryAuthFailed` au setup |
| `OneMinAIError` | Retourne erreur `IntentResponse` |
| Timeout (>60s) | Lève `OneMinAIError` |
| API 4xx/5xx | Parse body, log détail |
| JSON parse fail | Lève `OneMinAIError` |
| Exception local intents | Log & fallthrough à LLM |

## Points de performance

### Latence
- Setup: 1-2s (validation API)
- Requête chat: 5-30s (dépend du modèle/1min.ai)
- Local intent: <100ms

### Mémoire
- Cache max: 100 conversations × ~500B = ~50KB
- Client aiohttp: ~1MB

### Concurrence
- Utilise `async_timeout.timeout()` pour éviter les blocages
- `aiohttp.ClientSession` réutilisée

## Testing

Pas de tests unitaires requis pour HACS, mais pour développement:

```bash
# Debug logs
logger:
  logs:
    oneminai: debug

# Service de test (Developer Tools > Services)
service: oneminai.ask
data:
  prompt: "test"
  model: "gpt-4o-mini"
response_variable: result

# Vérifier la réponse
{{ result.response }}
```

## Modification future

### Ajouter un nouveau paramètre d'option

1. Ajouter à `const.py`:
```python
CONF_NEW_PARAM = "new_param"
DEFAULT_NEW_PARAM = "default_value"
```

2. Importer et ajouter au schéma dans `config_flow.py`:
```python
vol.Required(
    CONF_NEW_PARAM,
    default=options.get(CONF_NEW_PARAM, DEFAULT_NEW_PARAM),
): SelectorType(...)
```

3. Ajouter traduction dans `strings.json` et `translations/fr.json`

4. Utiliser dans `conversation.py`:
```python
options.get(CONF_NEW_PARAM, DEFAULT_NEW_PARAM)
```

### Support d'un nouveau modèle

Ajouter simplement à `SUPPORTED_MODELS` dans `const.py` — pas de code à changer.
