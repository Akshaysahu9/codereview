# CodeReview

Multi-language static code review tool — Python, JavaScript, TypeScript, Java, and C++.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-19-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)

## Features

- Code review with score (0–100)
- Bug detection (syntax, logic, security, loops)
- Complexity metrics
- Optimization suggestions
- Explain / Fix / Test scaffolds
- Review history (SQLite)
- Export report as Markdown
- Jump-to-line in editor

## Local setup

```powershell
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
scripts\install-engines.bat
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## GitHub upload (step by step)

### 1. Git identity — sirf tumhara naam

Contributor mein **sirf wahi dikhega jo tum commit karte ho**. Pehle yeh set karo:

```powershell
git config --global user.name "Your Full Name"
git config --global user.email "your-email@gmail.com"
```

> GitHub par sirf wahi naam dikhega jo `git config user.name` mein set ho. Apna personal email use karo.

### 2. GitHub par naya repo

1. https://github.com/new
2. Repository name: `codereview` (ya jo chaho)
3. **Public** select karo
4. README / .gitignore **mat** add karo (project pehle se hai)
5. **Create repository**

### 3. Project push karo

```powershell
cd path/to/codereview

git init
git add .
git status
```

Check karo `.env`, `venv`, `node_modules` staged **nahi** hone chahiye.

```powershell
git commit -m "Initial commit: CodeReview static analysis platform"

git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/codereview.git
git push -u origin main
```

Replace `YOUR_USERNAME` apne GitHub username se.

### 4. Verify contributors

Repo → **Insights** → **Contributors** — sirf **tumhara** naam hona chahiye.

---

## Live deploy

Project do parts mein hai:

| Part | Host | Why |
|------|------|-----|
| Frontend (React) | **Vercel** | Static site, free |
| Backend (FastAPI) | **Render** | Python server, free tier |

Vercel sirf frontend chala sakta hai; backend alag deploy karna padega.

### Step A — Backend on Render

1. https://render.com — sign up (GitHub se login)
2. **New +** → **Web Service**
3. Connect apna GitHub repo
4. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables:**
   - `FRONTEND_URL` = `https://your-app.vercel.app` (Vercel deploy ke baad daaloge)
6. **Create Web Service**
7. Copy URL — e.g. `https://codereview-api.onrender.com`

Health check: `https://YOUR-RENDER-URL.onrender.com/api/health`

### Step B — Frontend on Vercel

1. https://vercel.com — sign up (GitHub se)
2. **Add New** → **Project**
3. Import same GitHub repo
4. Settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. **Environment Variables:**
   - `VITE_API_URL` = `https://codereview-api.onrender.com` (Render URL, no trailing slash)
6. **Deploy**

Live site: `https://your-project.vercel.app`

### Step C — CORS fix

Render dashboard → backend service → **Environment** → update:

```
FRONTEND_URL=https://your-project.vercel.app
```

Save → service redeploy hoga.

---

## Project structure

```
codereview/
├── backend/          FastAPI + analyzers
├── frontend/         React + Vite
├── render.yaml       Render config (optional)
└── README.md
```

## License

MIT
