# Learnings

## Phase 0: Setup
- macOS ships Python 3.9; installed 3.12 with Homebrew and used a venv per project.
- API keys live in .env, which is git-ignored.
- gemini-2.5-flash was retired for new keys (404); switched to gemini-3.8-flash. Lesson: keep model names in config.
- Got a 503 (model overloaded); it passed on retry. Need retry with backoff later.
