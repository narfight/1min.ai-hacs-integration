# Changelog

Tous les changements notables de ce projet sont documentés dans ce fichier.

## [1.1.0] - 2025-01-15

### Added
- Support de Home Assistant 2025.1+ (minimum requis)
- Gestion de cache pour éviter les fuites mémoire
  - TTL de 1 heure par conversation
  - Limite max de 100 conversations simultanées
- Logging amélioré pour le debug
- Timeout configurable (par défaut 60s, au lieu de hardcodé 120s)
- Documentation complète (README.md)
- Support HACS officiel

### Changed
- Amélioration de la gestion des exceptions (plus précises)
- Stratégie "local d'abord" plus robuste avec meilleur logging
- Manifest.json conforme HACS

### Fixed
- Fuite mémoire sur `_remote_conversations`
- Gestion d'exceptions trop large dans `_async_try_local_intents`
- Logging dans exceptions demasiado verbosos

## [1.0.0] - 2024-XX-XX

### Initial Release
- Agent de conversation 1min.ai pour Home Assistant
- Stratégie "local d'abord" pour exécution locale des intents
- Support multi-modèles
- Recherche web optionnelle
- Historique conversationnel avec gestion du contexte
- Support images dans les prompts
- Support multilingue
