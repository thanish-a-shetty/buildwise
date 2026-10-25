# Learnings

## Phase 0: Setup
- macOS ships Python 3.9; installed 3.12 with Homebrew and used a venv per project.
- API keys live in .env, which is git-ignored.
- gemini-2.5-flash was retired for new keys (404); switched to gemini-3.8-flash. Lesson: keep model names in config.
- Got a 503 (model overloaded); it passed on retry. Need retry with backoff later.

## Phase 1: Ingestion
- PyMuPDF pages are 0-based; citations use page index + 1.
- PDF text comes out in drawing order: footers appeared first. Stripped header/footer lines.
- Kept line breaks so Phase 2 can split on clause numbers at line starts.
- BOQ tables read with pdfplumber; numbers arrive as strings with commas, converted with to_number().
- Each BOQ row becomes a readable sentence, because embeddings match sentences better than raw cells.
