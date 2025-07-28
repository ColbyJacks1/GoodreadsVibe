# Troubleshooting Guide

## Common Issues and Solutions

### 1. "not enough values to unpack (expected 2, got 1)" Error

**Cause**: This error typically occurs when the FastAPI backend is not running, causing the Streamlit frontend to receive unexpected response formats.

**Solution**:
1. Make sure the FastAPI backend is running first:
   ```bash
   poetry run uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
   ```

2. Then start the Streamlit frontend in a separate terminal:
   ```bash
   poetry run streamlit run ui/streamlit_app.py --server.port 8501
   ```

3. Or use the start script:
   ```bash
   python start_app.py
   ```

### 2. "Cannot connect to API server" Error

**Cause**: The FastAPI backend is not running or not accessible.

**Solution**:
1. Check if the backend is running on http://localhost:8000
2. Verify the API is accessible by visiting http://localhost:8000/docs
3. Make sure no other service is using port 8000

### 3. Poetry Command Not Found

**Cause**: Poetry is not in your PATH.

**Solution**:
```bash
export PATH="$HOME/Library/Python/3.13/bin:$PATH"
poetry --version
```

### 4. Missing Dependencies

**Cause**: Dependencies are not installed.

**Solution**:
```bash
poetry install
```

### 5. Database Issues

**Cause**: Database file is corrupted or missing.

**Solution**:
1. Delete the database file:
   ```bash
   rm embed_data.sqlite
rm -rf __pycache__
   ```

2. Recreate the sample database:
   ```bash
   poetry run python create_sample_db.py
   ```

### 6. Environment Variables

**Cause**: Missing required environment variables.

**Solution**:
1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   GOOGLE_GEMINI_API_KEY=your_google_gemini_key_here
   ```

### 7. Port Conflicts

**Cause**: Ports 8000 or 8501 are already in use.

**Solution**:
1. Find processes using the ports:
   ```bash
   lsof -i :8000
   lsof -i :8501
   ```

2. Kill the processes or use different ports:
   ```bash
   poetry run uvicorn app.api:app --reload --host 0.0.0.0 --port 8001
   poetry run streamlit run ui/streamlit_app.py --server.port 8502
   ```

### 8. SSL Certificate Issues

**Cause**: Network or SSL certificate problems.

**Solution**:
1. Check your internet connection
2. Try using a different network
3. If behind a corporate firewall, contact your IT department

## Debugging Steps

1. **Check Backend Status**:
   ```bash
   curl http://localhost:8000/
   ```

2. **Check Frontend Status**:
   ```bash
   curl http://localhost:8501/
   ```

3. **View Logs**:
   - Backend logs will appear in the terminal where you started uvicorn
   - Frontend logs will appear in the terminal where you started streamlit

4. **Test API Endpoints**:
   Visit http://localhost:8000/docs to test individual API endpoints

## Getting Help

If you're still experiencing issues:

1. Check the logs for specific error messages
2. Make sure all dependencies are installed: `poetry install`
3. Try recreating the database: `poetry run python create_sample_db.py`
4. Ensure both backend and frontend are running simultaneously

## Quick Start Checklist

- [ ] Poetry is installed and in PATH
- [ ] Dependencies are installed: `poetry install`
- [ ] Environment variables are set (if using external APIs)
- [ ] Backend is running: `poetry run uvicorn app.api:app --reload --host 0.0.0.0 --port 8000`
- [ ] Frontend is running: `poetry run streamlit run ui/streamlit_app.py --server.port 8501`
- [ ] Database exists (or run `poetry run python create_sample_db.py`)
- [ ] No port conflicts
- [ ] Internet connection is available (for external API calls) 