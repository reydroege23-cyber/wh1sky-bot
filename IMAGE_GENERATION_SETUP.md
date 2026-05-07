# 🎨 AI Image Generation Setup Guide

## Overview
This bot now supports AI image generation using the `!whisky` command!

## Installation

### 1. Get Hugging Face API Key
- Go to [Hugging Face](https://huggingface.co/)
- Sign up for a free account
- Go to Settings → Access Tokens
- Create a new token (read access is enough)
- Copy your token

### 2. Update .env File
Edit `.env` and replace:
```
HUGGINGFACE_API_KEY=hf_YOUR_HUGGINGFACE_TOKEN_HERE
```

With your actual token:
```
HUGGINGFACE_API_KEY=hf_abcdef1234567890...
```

### 3. Install Dependencies
```bash
pip install requests
```

## Usage

### Command Format
```
!whisky <prompt>
```

### Examples
```
!whisky cyberpunk wolf
!whisky anime girl with red eyes
!whisky futuristic city at night
!whisky painting of a dragon in fantasy style
!whisky realistic portrait of a person
```

### Features
- ✅ Async image generation
- ✅ Per-user cooldown (30 seconds default)
- ✅ Prompt length validation (max 200 characters)
- ✅ Loading message feedback
- ✅ Error handling
- ✅ User statistics tracking
- ✅ Timeout protection (60 seconds)

## Configuration

Edit `config.py` to customize:

```python
# Image generation settings
IMAGE_MODEL = "stabilityai/stable-diffusion-2-1"  # Change AI model
IMAGE_GENERATION_TIMEOUT = 60  # Timeout in seconds
IMAGE_COOLDOWN = 30  # Cooldown between generations (seconds)
MAX_PROMPT_LENGTH = 200  # Maximum prompt length
ENABLE_IMAGE_GENERATION = True  # Enable/disable feature
```

## Available Models

### Fast & Quality
- `stabilityai/stable-diffusion-2-1` (recommended)
- `runwayml/stable-diffusion-v1-5`
- `stabilityai/stable-diffusion-2`

### Other Options
- `prompthero/openjourney-v4`
- `stabilityai/stable-diffusion-xl-base-1.0`

## Troubleshooting

### "Failed to generate image"
- Check your Hugging Face API key is correct
- Verify you have enough credits/quota
- Try a different model

### "Prompt too long"
- Reduce your prompt to under 200 characters

### "Please wait before generating"
- You're on cooldown. Wait 30 seconds.

### Timeout Error
- The API is taking too long
- Try a simpler prompt
- Try again later

## Free Tier Limits

Hugging Face free tier includes:
- Limited API calls per month
- Slower inference times
- May queue requests during peak hours

For production/high usage, upgrade to Hugging Face Pro.

## Deployment on Railway

1. Add environment variable in Railway dashboard:
   ```
   HUGGINGFACE_API_KEY=hf_your_token_here
   ```

2. The bot will automatically use it on startup

3. No additional configuration needed!

## Advanced Features (Optional)

### Add Image Styles
```python
STYLES = {
    "anime": "anime art style",
    "realistic": "photorealistic",
    "cyberpunk": "cyberpunk style",
    "fantasy": "fantasy art"
}
```

Use: `!whisky anime:cyberpunk wolf`

### Admin-Only Mode
```python
@admin_only
async def handle_image_generation(update, context):
    # Only admins can generate images
```

### Generation Queue
```python
generation_queue = asyncio.Queue()
# Limit concurrent generations
```

## Support

For issues with:
- **Hugging Face**: Visit [Hugging Face Docs](https://huggingface.co/docs/api-inference)
- **Bot**: Check main.py error logs
- **Telegram**: Check telegram errors with /logs

---

Happy image generating! 🎨✨
