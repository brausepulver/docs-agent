# DocsAgent

DocsAgent is a document assistant that integrates with various platforms like Google Docs and GitHub, providing AI-powered assistance for document workflows.

## Project Structure

```
docsagent/
├── backend/         # FastAPI backend
│   ├── app/
│   │   ├── auth/   # Authentication logic
│   │   └── main.py
└── frontend/        # React frontend
    ├── src/
    ├── package.json
    └── vite.config.js
```

## Setup Instructions

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Auth0 account

### Backend Setup

1. Create and activate a Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` in `backend/` with:
```bash
cp .env.example .env
```

Fill in the required environment variables.

`CREDENTIALS_FILE` should point to the given `credentials.json` file (given in the submission form). Place in `/backend/credentials.json` to match the default setting.

Generate an encryption key and set the `ENCRYPTION_KEY` env var:
```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Start the database container:
```bash
docker run -d --name docs-agent-db -e POSTGRES_USER=docs_agent_user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=docs_agent -p 5432:5432 postgres:latest
```

By default this corresponds to the `DATABASE_URL` env var.

5. Start the development server:
```bash
uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`

6. Sign in with the agent user:
- A sign-in with Google form will open on first launch.
- Log in with the agent user try.doccy@gmail.com (given by the `AGENT_ID` env var).
- Continue.
- Select access to Drive and Docs.

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create `.env` file in `frontend/` with:
```env
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=docsagent-api
VITE_API_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Auth0 Setup

1. Create an Auth0 account at [auth0.com](https://auth0.com)

2. Create a new API:
   - Go to "Applications" → "APIs"
   - Click "+ Create API"
   - Name: "DocsAgent API"
   - Identifier: `docsagent-api`
   - Signing Algorithm: RS256
   - Click Create

3. Create a new Application:
   - Go to "Applications" → "Applications"
   - Click "+ Create Application"
   - Select "Single Page Application"
   - Name it "DocsAgent"

4. Configure Application Settings:
   - Find your application in the Auth0 dashboard
   - Add these URLs under "Allowed Callback URLs":
     ```
     http://localhost:5173,
     http://localhost:5173/callback
     ```
   - Add to "Allowed Logout URLs":
     ```
     http://localhost:5173
     ```
   - Add to "Allowed Web Origins":
     ```
     http://localhost:5173
     ```
   - Add to "Allowed Origins (CORS)":
     ```
     http://localhost:5173
     ```

5. Get your credentials:
   - Domain: Found under Application Settings
   - Client ID: Found under Application Settings
   - API Audience: The API identifier you created (`docsagent-api`)

## Development Notes

### Frontend

- Built with React + Vite
- Uses React Router for routing
- Auth0 for authentication
- Styling with vanilla CSS
- Lucide React for icons

Key features:
- Protected routes with authentication
- Direct Google OAuth login
- Responsive design
- Integration dashboard

### Backend

- Built with FastAPI
- JWT authentication with Auth0
- CORS configured for frontend
- Structured for scalability

## Deployment

For production deployment:

1. Backend:
   - Update CORS origins
   - Set up proper SSL/TLS
   - Configure proper logging
   - Use production-grade ASGI server (e.g., Gunicorn)

2. Frontend:
   - Build the production bundle:
     ```bash
     npm run build
     ```
   - Serve the `dist` directory
   - Update Auth0 callback URLs for production domain

3. Auth0:
   - Add production URLs to allowed URLs in Auth0 settings
   - Configure proper error pages
   - Set up proper social connection settings

## Tips & Troubleshooting

- If authentication isn't working:
  - Check Auth0 callback URLs
  - Verify API audience matches exactly
  - Check browser console for CORS errors
  - Verify environment variables are loaded

- For local development:
  - Frontend runs on port 5173 (Vite default)
  - Backend runs on port 8000 (FastAPI default)
  - Make sure both servers are running
  - Check `.env` files are properly configured
