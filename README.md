# Quizania — Hinglish Engineering Quiz

**AI-powered multiple-choice quiz covering Cloud, AI, Telecom, Linux, and Software Engineering**

Quizania is a small FastAPI application that serves a Hinglish-style 7-question multiple-choice quiz. The backend tries to generate quizzes from an LLM (configurable via environment variables); when no LLM key is available it falls back to a deterministic local generator. A small single-page frontend (static files) consumes the API and presents the quiz in a playful UI.

---

## Features

- FastAPI backend with two JSON endpoints:
  - GET /api/quiz — returns a 7-question QuizPayload (AI-generated when LLM is configured)
  - POST /api/score — accepts answers and returns score + per-question results
- Static single-page frontend (static/index.html, app.js, style.css)
- LLM integration (optional): uses HTTP client to call an LLM API when LLM_API_KEY is set
- Fallback quiz generator when LLM is unavailable

## Stack
- Language(s): Python (backend), HTML/CSS/JavaScript (frontend)
- Framework / runtime: FastAPI (served by Uvicorn)
- Notable libraries: fastapi, uvicorn, httpx, python-dotenv, pydantic

## Project layout

```text
.gitignore           # ignores and boilerplate
main.py              # FastAPI app and quiz logic (entrypoint)
requirements.txt     # Python dependencies
__pycache__/         # Python bytecode (ignored)
static/              # Frontend: index.html, app.js, style.css, timer.js
  index.html         # SPA UI
  app.js             # Fetches /api/quiz and posts /api/score; UI logic
  style.css          # Visual styles
```

How it fits together:
- main.py defines the FastAPI app, mounts the static directory at /static and exposes three routes: `/` (serves static/index.html), `/api/quiz` (GET), and `/api/score` (POST).
- The frontend requests `/api/quiz` to render seven questions and posts the user's answers to `/api/score` to compute the result.
- If an LLM API key is provided in the environment, main.py's ai_quiz() attempts to generate questions using a remote LLM; otherwise, the app uses fallback_quiz() to return a locally-generated quiz.

## API / Data model

- QuizQuestion
  - question: string
  - options: array[string] (length 4)
  - answer: string (one of the options)
  - explanation: string

- QuizPayload
  - questions: array[QuizQuestion] (length 7)
  - source: string ("AI-generated" or fallback description)

- AnswerSubmission (POST /api/score body)
  - answers: array[string] (selected answers in order)
  - questions: array[QuizQuestion] (the same array returned by /api/quiz)

- Response from POST /api/score
  - score: integer
  - total: integer
  - results: array[{correct: bool, answer: string, explanation: string}]

## Environment variables

- LLM_API_KEY (recommended for AI-generated quizzes): API key for the LLM service. If missing, the app uses the local fallback quiz generator.
- LLM_BASE_URL (optional): base URL for the LLM API (defaults to https://api.groq.com/openai/v1 in the code).
- LLM_MODEL (optional): model identifier used when calling the LLM (defaults to openai/gpt-oss-20b).

Note: main.py uses python-dotenv to load variables from a `.env` file in the project root.

## Install and run (local development)

1. Clone the repository

```bash
git clone https://github.com/RabindraMishra-AIDS/Quizania.git
cd Quizania
```

2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate     # Windows (PowerShell/Cmd)

pip install -r requirements.txt
```

3. (Optional) Add a `.env` file with your LLM key

Create a `.env` in the project root with:

```env
LLM_API_KEY=your_key_here
# optional
#LLM_BASE_URL=https://api.your-llm.com
#LLM_MODEL=your-model-id
```

4. Start the server with Uvicorn

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. Open the app in your browser

- Landing page: http://localhost:8000/
- API endpoints: http://localhost:8000/api/quiz

## Example API usage

Get a quiz (curl):

```bash
curl -s http://localhost:8000/api/quiz | jq '.'
```

Submit answers (replace with actual questions and chosen answers):

```bash
curl -s -X POST http://localhost:8000/api/score \
  -H "Content-Type: application/json" \
  -d '{"answers": ["a","b","c","d","e","f","g"], "questions": []}' | jq '.'
```

Note: The frontend (static/app.js) posts the real questions array it received from /api/quiz, so for accurate scoring you should post the same questions back.

## Development notes

- The LLM prompt and the validation rules for AI output live in main.py (see ai_quiz() and extract_json()). The ai_quiz() function performs schema validation and will raise an error if the LLM response doesn't match the expected structure; the server falls back to fallback_quiz() in that case.
- The fallback quiz generator (fallback_quiz()) constructs seven questions from the TOPICS list and uses Hinglish openers defined in HINGLISH_OPENERS.
- Frontend behaviour is implemented in static/app.js — look for functions `load()`, `render()`, and `score()`.

## Security & privacy

- Do not commit your LLM API key. Use `.env` (which is already loaded by python-dotenv) or other secret management.
- The project does not persist any user data; scoring happens in-memory and results are returned immediately.

## TODO / Improvements

- Add a Dockerfile and docker-compose for easier deployment.
- Add basic tests (pytest) for ai_quiz(), fallback_quiz(), and score endpoint.
- Rate-limiting / abuse-protection if deployed publicly.
- CI pipeline to run tests and linting.

## License

This repository does not include an explicit license file. Add a LICENSE if you want to permit reuse.

---

If you'd like, I can:
- open a pull request adding this README.md to the repository
- or add a Dockerfile and a GitHub Actions workflow to build and run the app

