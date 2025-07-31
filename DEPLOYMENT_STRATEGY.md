# 🚀 Two-Step Deployment Strategy

## Problem: AI Dependencies Are Too Heavy

Your AI app has heavy dependencies (PyTorch, CUDA packages) that cause build timeouts on free tiers.

## Solution: Deploy in Two Steps

### Step 1: Deploy Basic App (Fast)
1. **Use `requirements-light.txt`** (no PyTorch)
2. **App deploys quickly** (2-3 minutes)
3. **Basic features work** (inventory, projects, uploads)
4. **AI features disabled** but app is live

### Step 2: Add AI Features (Optional)
1. **Upgrade to paid plan** if needed
2. **Switch to full requirements**
3. **AI features become available**

## Quick Deploy Commands

### For Railway:
```bash
# Step 1: Deploy basic app
# Railway will use requirements-light.txt automatically

# Step 2: Add AI later (optional)
# Change railway.json to use requirements.txt
```

### For Render:
```bash
# Step 1: Deploy basic app
# Use requirements-light.txt

# Step 2: Add AI later (optional)
# Switch to requirements.txt
```

## What Works in Basic Mode:

✅ **User authentication** (login/register)  
✅ **Inventory management**  
✅ **Project tracking**  
✅ **Image uploads** (stored but not processed)  
✅ **Pre-stage helper**  
✅ **All web interface features**  

## What's Disabled in Basic Mode:

❌ **AI image processing**  
❌ **Similarity matching**  
❌ **Staged room suggestions**  

## Benefits:

1. **Fast deployment** (2-3 minutes vs 15+ minutes)
2. **No build timeouts**
3. **Works on all free tiers**
4. **Can add AI later** when needed
5. **Client can use basic features immediately**

## When to Add AI:

- **After successful basic deployment**
- **When client needs AI features**
- **When you can upgrade to paid plan**
- **When you have time to optimize**

## File Structure:

```
requirements-light.txt    # Basic dependencies (fast deploy)
requirements.txt          # Full dependencies (AI features)
railway.json             # Railway config (uses light requirements)
render.yaml              # Render config (can be updated)
```

This strategy gets your app live quickly, then you can add AI features when ready! 🎉 