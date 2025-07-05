# VaakShakti AI - Speech Tutor

VaakShakti AI is an intelligent speech tutor designed to help users improve their speaking skills. It provides interactive practice sessions, generates questions on various topics, transcribes user speech, and offers feedback on grammar, pronunciation, and content.

This project has been refactored into a full-stack application with a Python (FastAPI) backend, a PostgreSQL database for user management and history, and a Vite/React frontend. The entire application is containerized using Docker for ease of setup and deployment.

## Features

*   **Interactive Speech Practice:** Users can select topics and difficulty levels.
*   **AI-Generated Questions:** Get unique questions tailored to the chosen topic and difficulty.
*   **Speech Transcription:** User audio responses are transcribed using Whisper.
*   **Comprehensive Feedback:**
    *   Grammar analysis and corrections.
    *   Pronunciation tips for flagged words.
    *   Content evaluation compared to an ideal answer.
    *   Overall performance rating.
*   **User Authentication:** Secure registration and login for users.
*   **Personalized History:** Users can track their practice sessions and progress.
*   **Interview Preparation:** Generate tailored interview questions based on topic, personality, and skills.

## Architecture

The application consists of three main services managed by Docker Compose:

1.  **Backend (`speech-tutor` service):**
    *   Built with **FastAPI** (Python).
    *   Handles all business logic, API requests, LLM interactions (via Ollama), and database operations.
    *   Uses **SQLModel** as an ORM for PostgreSQL.
    *   Implements JWT for user authentication.
2.  **Database (`vaakshakti-db` service):**
    *   **PostgreSQL** database.
    *   Stores user accounts and practice session history.
3.  **Frontend (`vaakshakti-frontend` service):**
    *   Built with **Vite, React, and TypeScript**.
    *   Uses **shadcn-ui** and **Tailwind CSS** for styling.
    *   Served by **Nginx**.
    *   Communicates with the backend API.

## Technologies Used

**Backend:**
*   Python 3.10+
*   FastAPI
*   Uvicorn (ASGI server)
*   SQLModel (ORM)
*   PostgreSQL (via `asyncpg` driver)
*   Passlib (for password hashing)
*   PyJWT (for JSON Web Tokens)
*   Faster-Whisper (for speech-to-text)
*   Requests (for Ollama communication)

**Frontend:**
*   Vite
*   React
*   TypeScript
*   Bun (for package management and building the frontend)
*   Tailwind CSS
*   shadcn-ui (UI components)
*   React Router
*   React Query (TanStack Query)

**DevOps & Other:**
*   Docker & Docker Compose
*   Nginx (for serving frontend)
*   Ollama (for Large Language Model interactions - expected to be running separately and accessible by the backend)

## Project Structure

```
.
├── Dockerfile                  # For the FastAPI backend service
├── docker-compose.yml          # Defines all services (backend, db, frontend)
├── main.py                     # FastAPI application entry point
├── database.py                 # Database models and connection setup
├── security.py                 # Authentication utilities (hashing, JWT)
├── llm_engine.py               # Logic for LLM calls
├── whisper_engine.py           # Speech transcription logic
├── grammar_corrector.py        # Grammar and feedback logic
├── requirements.txt            # Python dependencies for backend
├── prompts/                    # Directory for LLM prompts
│   ├── correction_prompt.txt
│   ├── feedback_prompt.txt
│   └── question_prompt.txt
├── vaakshakti-speech-spark-backened/ # Frontend application
│   ├── Dockerfile              # For the Vite/React frontend service
│   ├── nginx.conf              # Nginx configuration for frontend
│   ├── package.json
│   ├── bun.lockb
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── public/
│   └── src/                    # Frontend source code (React components, services, etc.)
│       ├── App.tsx
│       ├── main.tsx
│       ├── services/api.ts
│       ├── contexts/AuthContext.tsx
│       ├── pages/
│       └── components/
└── README.md                   # This file
```

## Prerequisites

*   **Docker Desktop** (or Docker Engine + Docker Compose CLI) installed and running.
*   **Ollama** installed and running, with the necessary models pulled (e.g., `mistral:latest`). The backend expects to reach Ollama at `http://host.docker.internal:11434` (from within the backend Docker container, this refers to `localhost:11434` on your host machine).

## Getting Started

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```

2.  **Generate and Configure `SECRET_KEY`:**
    A strong `SECRET_KEY` is essential for securing JWT authentication.
    
    *   **Generate a key:** You can generate a secure key using Python. Open a Python interpreter and run:
        ```python
        import secrets
        print(secrets.token_hex(32))
        ```
        This will output a 64-character hexadecimal string (e.g., `b3a0e6f2d7c8a1b9e0f3d6c7b8a9d0e1c2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7`). Copy this generated key.

    *   **Set the key in `docker-compose.yml`:** Open the `docker-compose.yml` file in the project root. Locate the `speech-tutor` service and update the `SECRET_KEY` environment variable with your generated key:
        ```yaml
        services:
          speech-tutor:
            # ... other configurations
            environment:
              # ... other environment variables
              - SECRET_KEY: "PASTE_YOUR_GENERATED_KEY_HERE" # <-- CHANGE THIS!
        ```

3.  **Build and Run with Docker Compose:**
    From the project root directory, run:
    ```bash
    docker-compose up --build
    ```
    This command will:
    *   Build the Docker images for the backend and frontend services.
    *   Pull the PostgreSQL image.
    *   Start all three services.
    Wait for all services to initialize. You should see logs from each service in your terminal.

4.  **Access the Application:**
    *   **Frontend Application:** Open your web browser and navigate to `http://localhost:1213`
    *   **Backend API Documentation (Swagger UI):** Navigate to `http://localhost:1212/docs`

5.  **Register and Login:**
    Use the frontend interface at `http://localhost:1213` to register a new user account or log in with the demo accounts.

    **Demo User Accounts:**
    The application will attempt to create the following demo users on startup if they don't already exist:
    *   **User 1:**
        *   Email: `test@example.com`
        *   Password: `testpassword`
    *   **User 2:**
        *   Email: `user2@example.com`
        *   Password: `password123`

## Development Notes

*   **Backend API:** The FastAPI backend runs on port `8000` inside its container and is mapped to port `1212` on the host.
*   **Frontend (served by Nginx):** The production build of the frontend is served by Nginx on port `80` inside its container and is mapped to port `1213` on the host.
*   **Database (PostgreSQL):** Runs on port `5432` inside its container and is mapped to port `1211` on the host. Database credentials are set in `docker-compose.yml`.
*   **Frontend Local Development (Optional):** If you wish to run the frontend development server (with hot-reloading) locally while the backend runs in Docker:
    1.  Ensure the backend and database are running via `docker-compose up`.
    2.  Navigate to the `vaakshakti-speech-spark-backened/` directory.
    3.  Install dependencies: `bun install`
    4.  Start the dev server: `bun run dev`
        The frontend will be available at `http://localhost:8080` (or as configured in `vite.config.ts`). The Vite dev server proxy in `vite.config.ts` should forward API calls to the Dockerized backend at `http://localhost:1212`.

## Stopping the Application

To stop all services, press `Ctrl+C` in the terminal where `docker-compose up` is running.
To stop and remove the containers, you can run:
```bash
docker-compose down
```
To remove volumes as well (this will delete your database data):
```bash
docker-compose down -v
```

## Further Frontend Development

The primary remaining work involves updating the React components in `vaakshakti-speech-spark-backened/src/` to fully integrate with the new backend API and authentication system. This includes:
*   Refactoring `pages/Index.tsx` and its child components.
*   Updating `components/Header.tsx` for user status and login/logout.
*   Implementing UI for displaying user practice history.