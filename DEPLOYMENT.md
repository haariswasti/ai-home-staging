# AI Home Staging - Deployment Guide

## Quick Deploy to Render (Recommended)

### Step 1: Prepare Your Repository
1. Make sure all your code is committed to Git
2. Ensure you have these files in your root directory:
   - `app.py`
   - `requirements.txt`
   - `render.yaml`
   - `src/` folder with all your AI modules
   - `templates/` folder with HTML templates
   - `data/` folder with your staged images

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com) and create a free account
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Create Web Service"
6. Your app will be deployed in 5-10 minutes!

### Step 3: Set Environment Variables (Optional)
In Render dashboard, go to your service → Environment:
- `SECRET_KEY`: Generate a random secret key
- `DATABASE_URL`: Render will provide this automatically

## Alternative Deployment Options

### Heroku
```bash
# Install Heroku CLI
heroku create your-app-name
git push heroku main
```

### Railway
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repo
3. Deploy automatically

### DigitalOcean App Platform
1. Go to DigitalOcean App Platform
2. Connect your repository
3. Deploy with automatic scaling

## Post-Deployment

### 1. Test Your App
- Visit your deployed URL
- Test image upload functionality
- Verify AI matching works

### 2. Set Up Custom Domain (Optional)
- In Render: Go to your service → Settings → Custom Domains
- Add your domain and configure DNS

### 3. Monitor Performance
- Check Render logs for any errors
- Monitor response times
- Set up alerts if needed

## Troubleshooting

### Common Issues:
1. **Import Errors**: Make sure `src/` folder is included
2. **File Upload Issues**: Check upload folder permissions
3. **Database Errors**: Ensure database URL is correct
4. **Memory Issues**: Consider upgrading to paid plan for larger models

### Performance Tips:
1. Use CDN for static files
2. Optimize image sizes before upload
3. Consider caching for AI results
4. Use background jobs for heavy processing

## Security Considerations

1. **Change Default Passwords**: Update admin credentials
2. **Secure File Uploads**: Validate file types and sizes
3. **Environment Variables**: Never commit secrets to Git
4. **HTTPS**: Enable SSL certificates
5. **Rate Limiting**: Consider adding rate limits for uploads

## Scaling Your App

### When to Scale:
- High traffic (>1000 users/day)
- Large file uploads
- Complex AI processing

### Scaling Options:
1. **Render**: Upgrade to paid plan
2. **Load Balancing**: Use multiple instances
3. **CDN**: Serve static files globally
4. **Database**: Use managed database service 