# Free Hugging Face API Setup for Illustrations

## Why Hugging Face?
- ✅ **100% FREE** - No credit card required
- ✅ **No usage limits** for basic usage
- ✅ **High quality** Stable Diffusion XL images
- ✅ **Easy setup** - Takes 2 minutes

## Step-by-Step Setup

### 1. Create Hugging Face Account
1. Go to https://huggingface.co/join
2. Sign up with email (or GitHub/Google)
3. Verify your email

### 2. Generate API Token
1. Go to https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Name it: `SmartCourses` (or anything you like)
4. Role: Select **"Read"** (default)
5. Click **"Generate token"**
6. **Copy the token** (starts with `hf_...`)

### 3. Add to Your Project
1. Open `.env` file in your SmartCourses folder
2. Replace this line:
   ```
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   ```
   With:
   ```
   HUGGINGFACE_API_KEY=hf_YourActualTokenHere
   ```
3. Save the file
4. Restart your Django server

### 4. Test It!
1. Go to any course in your app
2. Click **"View Illustrations"**
3. Click **"Generate New"**
4. Enter a description like: "A colorful diagram of the solar system with labeled planets"
5. Make sure **"Hugging Face"** is selected
6. Click **"Generate Illustration"**
7. Wait 10-30 seconds

## Example Prompts

### Educational Diagrams
```
A detailed cross-section of a plant cell showing nucleus, chloroplasts, 
mitochondria, and cell wall, labeled, scientific illustration style
```

### Historical Scenes
```
Ancient Egyptian pyramids being built, workers moving stone blocks, 
desert landscape, historical accuracy, warm lighting
```

### Science Concepts
```
DNA double helix structure with base pairs highlighted, molecular 
visualization, educational diagram, vibrant colors
```

### Technology
```
Computer motherboard components labeled, circuit board, electronic 
components, technical illustration, high detail
```

## Tips for Best Results

1. **Be Specific**: More details = better images
2. **Add Style**: Include "scientific illustration", "diagram", "educational"
3. **Mention Colors**: "vibrant colors", "blue and white", etc.
4. **Include Context**: "on white background", "with labels", etc.
5. **Avoid Complex Scenes**: Focus on one main subject

## Troubleshooting

### "API key not configured" error
- Check that you copied the full token (starts with `hf_`)
- Make sure there are no extra spaces
- Restart the Django server after updating `.env`

### "Model is loading" error
- First request may take 20-30 seconds
- Hugging Face models need to "wake up"
- Try again after 30 seconds

### Image quality not good enough
- Add more details to your description
- Try different wording
- Use style keywords like "high quality", "detailed", "professional"

### Rate limits
- Free tier: ~1000 requests/month
- If you hit limits, wait 24 hours or create another account

## Alternative Free Options

If Hugging Face doesn't work:

1. **Stability AI Free Tier** (100 credits/month)
   - Sign up at https://platform.stability.ai
   - Add `STABILITY_API_KEY` to `.env`

2. **Local Generation** (Advanced)
   - Install Stable Diffusion locally
   - No API needed but requires powerful GPU

## Cost Comparison

| Provider | Cost | Quality | Speed |
|----------|------|---------|-------|
| **Hugging Face** | FREE ⭐ | Good | Medium |
| OpenAI DALL-E 3 | $0.04/image | Excellent | Fast |
| Stability AI | $0.002/image | Very Good | Fast |

## Support

If you need help:
1. Check the error message in Django console
2. Verify API key at https://huggingface.co/settings/tokens
3. Test the API key with a simple request

---

**Ready to generate amazing educational illustrations for FREE!** 🎨
