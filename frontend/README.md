# SocialPilot AI — Telegram Mini App Frontend

Mobile-first React frontend for **SocialPilot AI**, built for multi-tenant social media management directly inside Telegram.

---

## 🚀 Technology Stack

- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS (custom theme, brand colors, Telegram safe areas)
- **Routing**: React Router DOM (role-gated route architecture)
- **Telegram SDK**: Integration with official `telegram-web-app.js`
- **Icons**: Lucide React
- **API Client**: Centralized fetch wrapper with automatic JWT injection, error normalization, and mock fallback

---

## 👥 Three-Role System Architecture

| Role | Scope | Key Capabilities |
| :--- | :--- | :--- |
| **Platform Owner** | Global Platform | Reviews & approves pending company registrations, suspends/reactivates workspaces, inspects platform health. |
| **Company Admin** | Company Workspace | Manages workspace settings, connects Telegram channels, invites team members, reviews/approves posts, publishes. |
| **Content Creator** | Company Workspace | Drafts posts, uploads media, runs AI caption generator, submits posts for admin approval. |

---

## 🔌 API Integration Matrix

| Feature | Endpoint | HTTP Method | Real Backend Status |
| :--- | :--- | :--- | :--- |
| **Health Check** | `/api/v1/health` | `GET` | ✅ Fully Implemented |
| **Telegram Auth** | `/api/v1/auth/telegram` | `POST` | ✅ Fully Implemented (HMAC-SHA256 validation) |
| **Register Company** | `/api/v1/companies/register` | `POST` | ✅ Fully Implemented |
| **My Registrations** | `/api/v1/companies/registrations/me` | `GET` | ✅ Fully Implemented |
| **Get Company** | `/api/v1/companies/{company_id}` | `GET` | ✅ Fully Implemented |
| **Pending Companies** | `/api/v1/owner-admin/companies/pending` | `GET` | ✅ Fully Implemented (Platform Owner only) |
| **Approve Company** | `/api/v1/owner-admin/companies/{id}/approve`| `POST` | ✅ Fully Implemented |
| **Reject Company** | `/api/v1/owner-admin/companies/{id}/reject` | `POST` | ✅ Fully Implemented |
| **Request More Info**| `/api/v1/owner-admin/companies/{id}/request-info` | `POST` | ✅ Fully Implemented |
| **Posts & Drafts** | `/api/v1/companies/{id}/posts` | `GET / POST` | ⏳ Pending Backend Route (Mock Mode Supported) |
| **AI Generation** | `/api/v1/companies/{id}/ai/generate` | `POST` | ⏳ Pending Backend Route (Simulation Supported) |
| **Channel Connect** | `/api/v1/companies/{id}/channels` | `POST` | ⏳ Pending Backend Route (Mock Mode Supported) |

---

## 🛠️ Getting Started

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```env
VITE_API_BASE_URL=/api/v1
VITE_APP_NAME=SocialPilot AI
VITE_ENABLE_DEV_MODE=true
```

### 3. Start Development Server
```bash
npm run dev
```
The Vite development server runs at `http://localhost:5173`. API requests to `/api` are automatically proxied to the FastAPI backend at `http://127.0.0.1:8000`.

### 4. Build for Production
```bash
npm run build
```
Production assets are output to `dist/`.

---

## 📱 Testing Inside Telegram

1. Expose your local frontend to the internet using an HTTPS tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:5173
   # OR
   ngrok http 5173
   ```
2. Open Telegram and message **@BotFather**.
3. Use `/newapp` or `/myapps` to configure your bot's Mini App Web App URL to your tunnel's HTTPS URL (e.g. `https://your-tunnel.ngrok-free.app`).
4. Launch your bot on Telegram and open the Mini App!
