# Deployment Guide

Deploy your Claim Processing Pipeline to the cloud in minutes. Choose any of these platforms.

## Prerequisites

- GitHub account with the repository pushed
- Google API key (from GOOGLE_API_KEY)
- Cloud platform account (choose one below)

## Option 1: Render (Easiest)

Render is free for hobby tier and extremely beginner-friendly.

### Steps

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/vaishnavi-ai.git
   git push -u origin main
   ```

2. **Go to https://render.com**
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub account
   - Select the `vaishnavi-ai` repository

3. **Configure**
   - Name: `claim-processor` (or whatever you like)
   - Environment: `Python 3`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`

4. **Set Environment Variable**
   - Go to "Environment"
   - Add new variable:
     - Key: `GOOGLE_API_KEY`
     - Value: `AIza...` (your actual key)
   - Click "Save"

5. **Deploy**
   - Click "Create Web Service"
   - Wait ~2 minutes for deployment
   - Your URL: `https://claim-processor.onrender.com`

### Test
```bash
curl -X POST https://claim-processor.onrender.com/api/process \
  -F "claim_id=TEST-001" \
  -F "file=@sample_claim.pdf"
```

### Docs
Visit: `https://claim-processor.onrender.com/docs`

---

## Option 2: Railway

Railway is modern, powerful, and has a generous free tier.

### Steps

1. **Go to https://railway.app**
   - Click "Start a New Project"
   - Select "Deploy from GitHub"
   - Connect your GitHub account
   - Select `vaishnavi-ai` repo

2. **Configure**
   - Railway auto-detects Python
   - It will automatically run `pip install -r requirements.txt`

3. **Set Start Command**
   - In the dashboard, go to "Settings"
   - Set Procfile or start command:
     ```
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

4. **Set Environment Variable**
   - Click on "Variables"
   - Add:
     - Key: `GOOGLE_API_KEY`
     - Value: `AIza...`
   - Click "Save"

5. **Deploy**
   - Click "Deploy"
   - Watch the logs
   - You'll get a public URL

### Test
```bash
curl -X POST https://your-app.railway.app/api/process \
  -F "claim_id=TEST-001" \
  -F "file=@sample_claim.pdf"
```

---

## Option 3: Fly.io

Fly.io is excellent for apps that need to be always-on. Free tier limited but powerful.

### Steps

1. **Install Flyctl**
   ```bash
   # macOS
   brew install flyctl
   
   # Or visit https://fly.io/docs/getting-started/installing-flyctl/
   ```

2. **Create Fly Account**
   ```bash
   fly auth signup
   ```

3. **Launch App**
   ```bash
   cd vaishnavi_ai
   fly launch
   ```
   
   Answer prompts:
   - App name: `claim-processor` (or your choice)
   - Region: closest to you
   - Postgres database: No
   - Redis: No

4. **Set Environment Variable**
   ```bash
   fly secrets set GOOGLE_API_KEY=AIza...
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```
   
   Wait ~3 minutes. You'll get a URL like `https://claim-processor.fly.dev`

### Test
```bash
curl -X POST https://claim-processor.fly.dev/api/process \
  -F "claim_id=TEST-001" \
  -F "file=@sample_claim.pdf"
```

---

## Option 4: Heroku (Requires Credit Card)

Heroku's free tier was removed, but it's still a good option.

### Steps

1. **Install Heroku CLI**
   ```bash
   brew tap heroku/brew && brew install heroku
   ```

2. **Create Procfile**
   ```bash
   echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
   ```

3. **Deploy**
   ```bash
   heroku create claim-processor
   heroku config:set GOOGLE_API_KEY=AIza...
   git push heroku main
   ```

4. **View Logs**
   ```bash
   heroku logs --tail
   ```

---

## Comparison

| Platform | Free Tier | Setup Time | Cold Start | Best For |
|----------|-----------|-----------|-----------|----------|
| **Render** | Unlimited hobby | 5 min | ~5s | Learning, hobby projects |
| **Railway** | $5/month free | 5 min | ~2s | Growing projects |
| **Fly.io** | 3 shared-cpu-1x 256MB VMs | 5 min | <1s | Always-on apps |
| **Heroku** | Paid only | 10 min | ~10s | Production use |

### Recommendation for Students
- **Starting out?** → **Render** (easiest, most beginner-friendly)
- **Want better performance?** → **Railway** (fast, modern dashboard)
- **Need reliability?** → **Fly.io** (powerful infrastructure)

---

## Post-Deployment

### 1. Test Your Live API

```bash
# Test the endpoint
curl -X POST https://your-live-url/api/process \
  -F "claim_id=TEST-001" \
  -F "file=@sample_claim.pdf" \
  | python3 -m json.tool

# Test interactive docs
# Visit: https://your-live-url/docs
# Upload PDF from browser
```

### 2. Monitor & Logs

#### Render
- Dashboard → Logs tab

#### Railway
- Dashboard → Logs

#### Fly.io
```bash
fly logs
fly status
```

### 3. Custom Domain

All platforms support custom domains (e.g., `api.yourname.com`):
- Buy domain from Namecheap, GoDaddy, Route53, etc.
- Point DNS to your platform's nameservers
- Configure in platform dashboard

---

## Environment Variables

All platforms securely store environment variables. You need:

```
GOOGLE_API_KEY=AIza...
```

**Important**: Never commit your API key to GitHub!

---

## Troubleshooting

### "Module not found"
**Problem**: Missing dependency
**Solution**: Check `requirements.txt` includes all packages
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
# Redeploy
```

### "GOOGLE_API_KEY not found"
**Problem**: Environment variable not set
**Solution**: 
- Render: Go to Environment → add variable
- Railway: Go to Variables → add variable
- Fly.io: Run `fly secrets set GOOGLE_API_KEY=...`

### "Build fails"
**Problem**: Often Python version mismatch
**Solution**: Create `runtime.txt`
```bash
echo "python-3.11.7" > runtime.txt
git add runtime.txt
git commit -m "Specify Python version"
git push
# Redeploy
```

### "Timeout processing PDF"
**Problem**: Large PDF or slow Gemini API
**Solution**: Increase timeout in platform settings
- Render: Settings → Timeout (default 30s)
- Railway: Set `MAX_REQUEST_SIZE`
- Fly.io: No default timeout (good for this use case)

---

## Cost Estimates

| Platform | Free Tier | Typical Cost |
|----------|-----------|--------------|
| **Render** | Unlimited | $7/month (hobby) |
| **Railway** | $5/month | $5-20/month |
| **Fly.io** | Included | $5-15/month |
| **Gemini API** | 15 req/min free | $0.001 per claim |

**Monthly usage**: 1000 claims/month
- Render/Railway/Fly.io: ~$7-15
- Gemini API: ~$1
- **Total**: ~$10/month

---

## Sharing Your Live API

Once deployed, share:

1. **API URL**: `https://claim-processor.onrender.com`
2. **Docs URL**: `https://claim-processor.onrender.com/docs`
3. **GitHub Repo**: `https://github.com/yourname/vaishnavi-ai`
4. **Quick Test Command**:
   ```bash
   curl -X POST https://claim-processor.onrender.com/api/process \
     -F "claim_id=TEST-001" \
     -F "file=@sample.pdf"
   ```

---

## Advanced: CI/CD Automatic Deployment

Set up automatic deployment whenever you push to GitHub:

### Render (Auto-enabled)
- Just connect GitHub
- Every `git push` automatically deploys

### Railway
- Go to Project Settings
- Enable "Deploy on push"
- Connect GitHub branch

### Fly.io
```bash
# Deploy via GitHub Actions (set up once)
fly tokens create deploy -x 336h
# Add token to GitHub Secrets
# Create .github/workflows/deploy.yml
```

---

## Next Steps

1. ✅ Deploy to your chosen platform
2. ✅ Test live API with sample PDF
3. ✅ Share live URL with friends/colleagues
4. ✅ Monitor logs for any issues
5. ✅ Record video explanation (see VIDEO_GUIDE.md)
6. ✅ Share on GitHub, LinkedIn, portfolio

---

**Congratulations! Your AI claim processor is now live on the internet.** 🚀
