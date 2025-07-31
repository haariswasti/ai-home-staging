# 🚀 Quick Start Guide

## Deploy Your Website (5 minutes)

### Step 1: Deploy to Render
1. **Go to [render.com](https://render.com)** and sign up for free
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Render will auto-detect your `render.yaml` file**
5. **Click "Create Web Service"**
6. **Wait 5-10 minutes for deployment**

Your website will be live at: `https://your-app-name.onrender.com`

### Step 2: Test Your Deployment
- Visit your live URL
- Create an account and login
- Upload a photo to test AI matching
- Verify all features work

## Add More Photos (Improve AI)

### Step 1: Collect Photos
**Free Sources:**
- [Unsplash](https://unsplash.com/s/photos/bedroom) - Search "bedroom", "living room", etc.
- [Pexels](https://www.pexels.com/search/bedroom/) - High-quality free photos
- [Pixabay](https://pixabay.com/images/search/bedroom/) - Free stock photos

**Professional Sources:**
- [Houzz](https://www.houzz.com) - Professional staging photos
- [Pinterest](https://www.pinterest.com) - Search "staged bedroom"
- Real estate websites (Zillow, Redfin)

### Step 2: Organize Photos
```bash
# Create directories for all room types
python add_photos.py --create-dirs

# See current photo count
python add_photos.py --count
```

### Step 3: Add Photos
```bash
# Add staged bedroom photos
python add_photos.py --add "C:/path/to/bedroom/photos" bedroom staged

# Add living room photos
python add_photos.py --add "C:/path/to/living/photos" living_room staged

# Generate new embeddings
python add_photos.py --generate-embeddings
```

### Step 4: Test Improvements
- Upload a new photo to your website
- See if AI matches are better
- Repeat with more photos for better results

## Quick Commands

### Check Current Status
```bash
python add_photos.py --count
```

### Add Photos from Folder
```bash
python add_photos.py --add "C:/Photos/Bedrooms" bedroom staged
python add_photos.py --add "C:/Photos/Living" living_room staged
python add_photos.py --add "C:/Photos/Kitchen" kitchen staged
```

### Update AI Model
```bash
python add_photos.py --generate-embeddings
```

## Room Types Supported

- **bedroom** - All bedroom types
- **living_room** - Living rooms, family rooms
- **dining_room** - Dining rooms, eat-in kitchens
- **kitchen** - Kitchens, kitchenettes
- **bathroom** - Bathrooms, powder rooms
- **office** - Home offices, studies
- **outdoor** - Patios, decks, gardens
- **entryway** - Foyers, entry halls
- **basement** - Finished basements
- **laundry** - Laundry rooms
- **garage** - Garages, workshops
- **patio** - Outdoor living spaces
- **deck** - Wooden decks
- **garden** - Landscaped areas

## Tips for Better AI Results

### Photo Quality
- **Resolution**: Minimum 800x600, ideally 1920x1080+
- **Lighting**: Well-lit, clear photos
- **Angles**: Wide shots showing the whole room
- **Style**: Variety of styles (modern, traditional, minimalist)

### Quantity
- **Minimum**: 20 photos per room type
- **Good**: 50 photos per room type
- **Excellent**: 100+ photos per room type

### Variety
- Different color schemes
- Various furniture styles
- Multiple layouts
- Different lighting conditions

## Troubleshooting

### Deployment Issues
- Check Render logs for errors
- Ensure all files are committed to Git
- Verify `requirements.txt` is up to date

### Photo Issues
- Use JPG, PNG, or JPEG format
- Keep files under 10MB
- Minimum 400x400 pixels
- Avoid blurry or dark photos

### AI Performance
- More photos = better matches
- Higher quality photos = better results
- Regular updates improve accuracy

## Next Steps

1. **Deploy your website** (5 minutes)
2. **Add 50+ photos per room type** (1-2 hours)
3. **Test and improve** (ongoing)
4. **Share with users** and get feedback
5. **Scale up** based on usage

## Support

- Check the `DEPLOYMENT.md` for detailed deployment info
- Read `AI_IMPROVEMENT_GUIDE.md` for advanced improvements
- Use `add_photos.py --help` for command help

Your AI home staging website is ready to go live! 🎉 