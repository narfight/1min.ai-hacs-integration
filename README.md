*Please :star: this repo if you find it useful*

# 1min.ai for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Replace Home Assistant's default conversation agent with a powerful AI-driven assistant powered by [1min.ai](https://1min.ai). Supports multi-model switching (GPT-4, Claude, Gemini, Mistral, etc.), web search, and conversational history.

# How it works

The integration acts as your Home Assistant conversation agent and follows this flow:

1. **User sends a prompt** via Assist (voice or text)
2. **Local intent matching** - Attempts to handle home automation commands locally (lights, switches, covers, etc.)
3. **If no local match** → Sends request to 1min.ai API with conversational context
4. **Response** returned to user

This "local-first" strategy keeps simple commands fast and instant, while complex queries leverage AI models for intelligent responses.

**Supported entity domains for local execution:**
- `light`, `cover`, `switch`, `media_player`, `input_select`
- Any entity with `on`/`off` states

# Pre-requisites

- **Home Assistant** ≥ 2025.1
- **Internet connectivity** (1min.ai API calls)
- **1min.ai API key** from [1min.ai](https://1min.ai)
- *(Optional)* `history` integration for maintaining conversational context (enabled by default)

# Installation

## Option 1 (Recommended)
- Have [HACS](https://hacs.xyz/) installed
- Click the button below to add the repository and install:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=narfight&repository=1min.ai-hacs-integration&category=integration)

- Or search for "1min.ai" in HACS Integrations and click Install
- Restart Home Assistant

## Option 2
- In your Home Assistant config directory (`~/.homeassistant`), create `custom_components/oneminai/`
- Clone this repository into that directory
- Restart Home Assistant

## Option 3
```bash
cd ~/.homeassistant/custom_components
git clone https://github.com/narfight/1min.ai-hacs-integration.git oneminai
# Restart Home Assistant
```

# Configuration

Click the button below to start setup:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=oneminai)

Or manually:
1. [![Open your Home Assistant instance and show your integrations.](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)
2. Click "+ Create Integration"
3. Search for "1min.ai"
4. Enter your **1min.ai API key**
5. Click Submit

You can customize options afterward by clicking **Options** on the integration card.

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| **AI Model** | Which model to use | `gpt-4o-mini` |
| **System Prompt** | Custom instructions for the AI | English/French (auto-detected) |
| **Local Control First** | Try local intents before API | `true` |
| **Web Search** | Enable web search in responses | `false` |
| **Number of Search Sites** | Web search results to fetch | `3` |
| **Max Search Words** | Word limit for extracted content | `1000` |
| **Request Timeout** | API response timeout (seconds) | `60` |
| **History Limit** | Conversation messages to keep | `10` |

## Supported Models

Indicative list (availability depends on your 1min.ai account):

- **OpenAI**: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`
- **Anthropic**: `claude-3-5-sonnet-20240620`, `claude-3-haiku-20240307`
- **Google**: `gemini-1.5-pro`, `gemini-1.5-flash`
- **Other**: `mistral-large-latest`, `deepseek-chat`

# Use it

The integration becomes your default Assist agent immediately after setup.

## Via Voice Assistant (Assist)

Simply speak to your Home Assistant:

```
"Turn on the living room"      → Executed locally (instant)
"What's the weather tomorrow?" → API call with web search
"Tell me a joke"               → Multi-model response
"Summarize the news"           → Web search + synthesis
```

## Via `oneminai.ask` Service

Call the integration directly from automations. Open your automations:

[![Open your Home Assistant instance and show your automations.](https://my.home-assistant.io/badges/automations.svg)](https://my.home-assistant.io/redirect/automations/)

Example automation:

```yaml
service: oneminai.ask
data:
  prompt: "Summarize the last 3 messages from my chat group"
  model: "gpt-4o"              # Optional, overrides config
  web_search: true             # Optional
response_variable: ia_response
```

Retrieve the response in a subsequent action:

```yaml
- service: notify.telegram
  data:
    message: "{{ ia_response.response }}"
```

# Advanced

## Debugging

Enable debug logging by clicking here to view your logs:

[![Open your Home Assistant instance and show the logs.](https://my.home-assistant.io/badges/logs.svg)](https://my.home-assistant.io/redirect/logs/)

Then add to your `configuration.yaml`:

```yaml
logger:
  logs:
    oneminai: debug
```

Check the logs for detailed request/response traces.

## Events

The integration fires no public events (future enhancement).

## Multiple Instances

You can create multiple 1min.ai integrations with different configurations (different models, prompts, etc.) by repeating the setup flow.

# Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Invalid API Key"** | Verify the key on [1min.ai dashboard](https://1min.ai), check internet connectivity |
| **"Timeout"** | Increase `Request Timeout` in options (max 120s), verify 1min.ai API status |
| **No local intent match** | Normal behavior — falls back to 1min.ai API for non-home-automation queries |
| **No conversation history** | Ensure `History Limit > 0` in options; history persists per conversation thread |
| **Model not available** | Check your 1min.ai account plan; some models require paid subscriptions |

# Resources

- 📖 [1min.ai Documentation](https://docs.1min.ai/)
- 🐛 [Report Issues](https://github.com/narfight/1min.ai-hacs-integration/issues)  
- 💬 [GitHub Discussions](https://github.com/narfight/1min.ai-hacs-integration/discussions)

Or access Home Assistant resources:

[![Open your Home Assistant instance and show the developer tools.](https://my.home-assistant.io/badges/developer_states.svg)](https://my.home-assistant.io/redirect/developer_states/)

# License

MIT License - See LICENSE file

---

*This integration was created whit Claude.ai*