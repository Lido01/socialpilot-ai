
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()


def generate_social_post(topic: str) -> str:
    """Generate a social media draft using Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash-lite",
    )

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a professional social media content writer.

Create ONE engaging social media post based on the topic below.

Requirements:
- Write a clear, natural caption.
- Start with an interesting hook.
- Include a relevant call to action.
- Use a few relevant hashtags.
- Keep the post concise and easy to read.
- Do not invent prices, discounts, locations, or business facts.
- Do not claim that an offer or promotion exists unless provided.

Topic supplied by the user:
{topic}

Return only the proposed post text.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    post_text = (response.text or "").strip()

    if not post_text:
        raise RuntimeError("The AI returned an empty response.")

    return post_text
