# Free Hosting Deployment Guide

This guide explains how to deploy the Hostel Management System using free hosting services: Netlify (frontend), Render (backend), and Supabase/Neon (database).

## Architecture Overview

```
User Browser → Netlify (Frontend) → Render (API Backend) → Supabase/Neon (Database)
```

## Prerequisites

1. GitHub account
2. Supabase or Neon account (for PostgreSQL database)
3. Render account
4. Netlify account

## Step 1: Set up Database (Supabase or Neon)

### Option A: Supabase (Recommended)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to Settings → Database → Connection string
4. Copy the connection string (it should look like: `postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres`)

### Option B: Neon

1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project
3. Copy the connection string from the dashboard

## Step 2: Set up Backend on Render

1. Go to [render.com](https://render.com) and create a free account
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `hostel-management-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

5. Add Environment Variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `CORS_ORIGINS`: `https://your-netlify-site.netlify.app` (update after Netlify deployment)
   - `GROQ_API_KEY`: Your Groq API key
   - `LANGSMITH_API_KEY`: Your LangSmith API key
   - `LANGSMITH_PROJECT`: `Hostel_Management_System`
   - `LANGSMITH_ENDPOINT`: `https://api.smith.langchain.com`
   - `LANGSMITH_TRACING`: `true`

6. Click "Create Web Service"
7. Wait for deployment to complete
8. Copy the service URL (e.g., `https://hostel-management-api.onrender.com`)

## Step 3: Set up Frontend on Netlify

1. Go to [netlify.com](https://netlify.com) and create a free account
2. Click "Add new site" → "Import an existing project"
3. Connect your GitHub repository
4. Configure the build settings:
   - **Base directory**: (leave empty)
   - **Build command**: `python build_frontend.py`
   - **Publish directory**: `dist`

5. Add Environment Variables (if needed):
   - Any frontend-specific variables

6. Click "Deploy site"
7. Wait for deployment to complete
8. Copy the site URL (e.g., `https://amazing-site.netlify.app`)

## Step 4: Update CORS Configuration

1. Go back to your Render service
2. Update the `CORS_ORIGINS` environment variable with your Netlify URL:
   - `CORS_ORIGINS`: `https://amazing-site.netlify.app`

3. Redeploy the Render service

## Step 5: Update Netlify Redirects

1. In your repository, update `netlify.toml`:
   ```toml
   [[redirects]]
     from = "/api/*"
     to = "https://hostel-management-api.onrender.com/api/:splat"
     status = 200

   [[redirects]]
     from = "/static/*"
     to = "https://hostel-management-api.onrender.com/static/:splat"
     status = 200

   [[redirects]]
     from = "/*"
     to = "https://hostel-management-api.onrender.com/:splat"
     status = 200
   ```

2. Replace `https://hostel-management-api.onrender.com` with your actual Render URL

3. Commit and push the changes
4. Netlify will automatically redeploy

## Step 6: Database Migration

After the first deployment, you need to run database migrations:

1. Go to your Render service logs
2. Check if the database tables were created automatically
3. If not, you may need to run migrations manually

## Environment Variables Summary

### Render (Backend)
```bash
DATABASE_URL=postgresql://...
CORS_ORIGINS=https://your-netlify-site.netlify.app
GROQ_API_KEY=your-groq-key
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=Hostel_Management_System
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING=true
```

### Netlify (Frontend)
No environment variables required (proxies to backend)

## Testing the Deployment

1. Visit your Netlify URL
2. Try logging in with admin credentials
3. Test the agent chat functionality
4. Verify database operations work

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure `CORS_ORIGINS` in Render matches your Netlify URL exactly
2. **Database Connection**: Verify your PostgreSQL connection string is correct
3. **API Calls Failing**: Check that Netlify redirects are pointing to the correct Render URL
4. **Static Files Not Loading**: Ensure the `/static/*` redirect is configured correctly

### Logs

- **Render Logs**: Check service logs in Render dashboard
- **Netlify Logs**: Check deploy logs and function logs in Netlify dashboard
- **Database Logs**: Check Supabase/Neon dashboard for connection issues

## Free Tier Limits

- **Supabase**: 500MB database, 50MB file storage
- **Neon**: 512MB storage, 100 hours compute time/month
- **Render**: 750 hours/month, sleeps after 15 minutes of inactivity
- **Netlify**: 100GB bandwidth/month, unlimited sites

## Security Considerations

1. Never commit API keys to GitHub
2. Use environment variables for all secrets
3. Regularly rotate API keys
4. Monitor service usage and costs
5. Set up proper CORS policies

## Cost Optimization

1. Render services sleep after inactivity - this is normal
2. Monitor your usage in each platform's dashboard
3. Set up alerts for usage limits
4. Consider upgrading plans as your usage grows

## Support

If you encounter issues:
1. Check the logs in each service
2. Verify environment variables are set correctly
3. Test database connectivity
4. Ensure all URLs are updated correctly in configuration files
