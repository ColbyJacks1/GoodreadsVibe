# 🚀 Deployment Guide

## Overview
This guide covers deploying your Goodreads Analyzer to various cloud platforms.

## 📋 Pre-Deployment Checklist

### ✅ Required Changes Made
- [x] Created `requirements.txt` for non-Poetry platforms
- [x] Added Streamlit configuration (`.streamlit/config.toml`)
- [x] Database supports `DATABASE_URL` environment variable
- [x] All AI modules load environment variables correctly

### 🔑 Environment Variables Needed
```bash
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=your_database_url (optional, defaults to SQLite)
```

## 🌐 Deployment Options

### 1. Streamlit Cloud (Recommended) ⭐⭐⭐⭐⭐

**Pros:**
- Native Streamlit hosting
- Free tier available
- Automatic deployment from GitHub
- Easy environment variable management

**Steps:**
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set environment variables in the dashboard
5. Deploy!

**Configuration:**
- **Main file path**: `ui/streamlit_app.py`
- **Python version**: 3.13
- **Environment variables**: Set in Streamlit Cloud dashboard

### 2. Railway ⭐⭐⭐⭐

**Pros:**
- Simple git-based deployment
- Good free tier ($5/month after)
- PostgreSQL database support
- Automatic HTTPS

**Steps:**
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy: `railway up`

**Configuration:**
- **Build command**: `pip install -r requirements.txt`
- **Start command**: `streamlit run ui/streamlit_app.py --server.port $PORT`

### 3. Heroku ⭐⭐⭐

**Pros:**
- Well-established platform
- Good documentation
- PostgreSQL add-on available

**Cons:**
- No free tier anymore
- More complex setup

**Steps:**
1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: streamlit run ui/streamlit_app.py --server.port $PORT --server.address 0.0.0.0
   ```
3. Deploy: `git push heroku main`

## 🔧 Platform-Specific Configurations

### Streamlit Cloud
- **No additional files needed**
- Environment variables set in dashboard
- Automatic HTTPS

### Railway
- **No additional files needed**
- Environment variables set in dashboard
- Automatic HTTPS

### Heroku
- **Procfile required** (see above)
- **Buildpacks**: Python buildpack
- **Add-ons**: PostgreSQL (optional)

## 🗄️ Database Options

### SQLite (Default)
- **Good for**: Simple deployments, low traffic
- **Limitation**: Single file, not suitable for high concurrency

### PostgreSQL (Recommended for Production)
- **Good for**: Multiple users, high traffic
- **Setup**: Use platform's PostgreSQL add-on
- **Connection**: Set `DATABASE_URL` environment variable

## 🔒 Security Considerations

### API Key Management
- ✅ Never commit API keys to Git
- ✅ Use environment variables
- ✅ Rotate keys regularly

### Data Privacy
- ✅ User data is session-based (not persistent across sessions)
- ✅ Consider adding user authentication for production

## 📊 Monitoring & Analytics

### Streamlit Cloud
- Built-in analytics dashboard
- Usage statistics available

### Other Platforms
- Use platform's monitoring tools
- Consider adding logging

## 🚀 Quick Deploy Commands

### Streamlit Cloud
```bash
# 1. Push to GitHub
git push origin main

# 2. Go to share.streamlit.io and connect repo
# 3. Set environment variables
# 4. Deploy!
```

### Railway
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway init
railway up
```

### Heroku
```bash
# 1. Create Heroku app
heroku create your-app-name

# 2. Set environment variables
heroku config:set GOOGLE_GEMINI_API_KEY=your_key

# 3. Deploy
git push heroku main
```

## 🎯 Recommended Approach

**For your use case, I recommend Streamlit Cloud because:**
1. **Perfect fit**: Native Streamlit hosting
2. **Easy setup**: Just connect GitHub repo
3. **Free tier**: Available for reasonable usage
4. **No configuration**: Works out of the box

## 📞 Support

If you encounter issues:
1. Check platform-specific logs
2. Verify environment variables are set
3. Test locally with same environment variables
4. Check platform documentation

---

**Happy Deploying! 🚀📚** 