#!/usr/bin/env python3
"""
Gemini Image Generator - Helper script for text-to-image and image-to-image tasks.

Usage:
    generate_image.py --prompt "description" [--model model_name] [--image path/to/image] [--output filename.png]
"""

import argparse
import sys
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

def generate_image(prompt, model="gemini-2.5-flash-image", image_path=None, output="generated_image.png"):
    """
    Generate or edit an image using the Gemini API.
    """
    try:
        client = genai.Client()
        contents = [prompt]
        
        if image_path:
            img = Image.open(image_path)
            contents.append(img)
            
        config = types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
        )
        
        # Use Gemini 3 Pro specific configs if applicable
        if model == "gemini-3-pro-image-preview":
             # Defaulting to 1:1 and 1K for simplicity in script, 
             # can be extended with more CLI args
             config.image_config = types.ImageConfig(
                 aspect_ratio="1:1",
                 image_size="1K"
             )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        for part in response.parts:
            if part.inline_data is not None:
                generated_img = part.as_image()
                generated_img.save(output)
                print(f"✅ Image saved as {output}")
                return True
            elif part.text:
                print(f"Part Text: {part.text}")
                
        print("❌ No image data found in response.")
        return False

    except Exception as e:
        print(f"❌ Error generating image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate images with Gemini")
    parser.add_argument("--prompt", required=True, help="Text description of the image")
    parser.add_argument("--model", default="gemini-2.5-flash-image", 
                        choices=["gemini-2.5-flash-image", "gemini-3-pro-image-preview"],
                        help="Gemini model to use")
    parser.add_argument("--image", help="Optional path to reference image for editing")
    parser.add_argument("--output", default="generated_image.png", help="Output filename")

    args = parser.parse_args()

    success = generate_image(args.prompt, args.model, args.image, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
