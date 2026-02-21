# ⚖️ ClauseGuard — AI Contract Risk Analyzer

> Know what you're signing. Built with Django + AI.

---

## 🚀 Local Setup (Step by Step)

### 1. Clone & navigate
```bash
cd clauseguard
```

### 2. Create virtual environment
```bash
python -m venv venv

# Activate:
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Then load them:
```bash
# Mac/Linux:
export $(cat .env | xargs)

# Windows PowerShell:
Get-Content .env | ForEach-Object { $k,$v = $_ -split '=',2; [System.Environment]::SetEnvironmentVariable($k,$v) }
```

### 5. Run the server
```bash
python manage.py runserver
```

Visit → **http://127.0.0.1:8000**

---

## 📁 Project Structure

```
clauseguard/
├── clauseguard/             # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── analyzer/                # Main app
│   ├── templates/analyzer/
│   │   ├── base.html        # Shared layout
│   │   ├── index.html       # Upload page
│   │   └── results.html     # Analysis results
│   ├── static/analyzer/
│   │   ├── css/main.css     # All styles
│   │   └── js/main.js       # Frontend logic
│   ├── services.py          # AI + PDF logic
│   ├── views.py             # Django views
│   └── urls.py              # URL routes
├── requirements.txt
├── manage.py
└── Procfile                 # For deployment
```

---

## 🌐 Deploy to Render

1. Push to GitHub
2. Create **Web Service** on [render.com](https://render.com)
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `gunicorn clauseguard.wsgi --log-file -`
5. Add Environment Variables:
   - `ANTHROPIC_API_KEY` = your key
   - `DJANGO_SECRET_KEY` = a long random string
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `your-app.onrender.com`

---

## 🔑 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Upload page |
| GET | `/results/` | Results page |
| POST | `/api/analyze-pdf/` | Upload & analyze PDF |
| POST | `/api/analyze-text/` | Analyze raw text |

---

## ⚠️ Disclaimer

ClauseGuard is not a substitute for professional legal advice.
