---
name: gemini-image-gen
description: This skill should be used when image generation, editing, or multi-turn visual refinement is required using Gemini 2.5 Flash or Gemini 3 Pro models. It enables high-fidelity text rendering, branding, and complex asset production.
---

# Gemini Image Generation

## Overview

This skill enables advanced image generation and conversational editing using the latest Gemini models. It provides specialized workflows for text-to-image, image-to-image refinement, and high-fidelity asset production with precise text rendering.

## Core Capabilities

### 1. Model Selection
Determine the appropriate model based on the requirement:
- **Gemini 2.5 Flash** (`gemini-2.5-flash-image`): Use for fast generation and basic editing tasks.
- **Gemini 3 Pro** (`gemini-3-pro-image-preview`): Use for professional assets, 4K resolution, complex reasoning, and multi-image consistency.

### 2. Basic Image Generation
To generate an image from a text description:
- Define a clear, descriptive prompt specifying subject, style, and lighting.
- Execute the generation using `scripts/generate_image.py`.
- Example: `python scripts/generate_image.py --prompt "A futuristic cityscape in watercolor style"`

### 3. Image Editing and Refinement
To modify an existing image:
- Provide the source image and a text prompt describing the change.
- Use Gemini 3 Pro for complex edits requiring grounding or character consistency.
- Example: `python scripts/generate_image.py --prompt "Add a floating island to the background" --image input.png`

### 4. Professional Asset Production (Gemini 3 Pro)
To produce high-resolution assets with legible text:
- Specify the resolution ("1K", "2K", "4K") and aspect ratio in the configuration.
- Reference `references/gemini_api.md` for specific technical parameters.
- Utilize "Grounding" with Google Search for factual accuracy if needed.

### 5. Advanced Prompt Engineering
To achieve professional results:
- Incorporate subject, composition, action, location, and style into every prompt.
- Reference `references/prompting_tips.md` for detailed guidance on cinematography, lighting, and multi-image consistency.

## Workflow Patterns

1. **Initial Draft**: Generate a base image using Gemini 2.5 Flash for speed.
2. **Review and Iterate**: Conversationaly refine the draft over multiple turns.
3. **Professional Finalization**: Re-generate or upscale the final version using Gemini 3 Pro with specific resolution and aspect ratio settings.

## Resources

- **scripts/generate_image.py**: CLI tool for executing generation and editing tasks.
- **references/gemini_api.md**: Technical reference for models, aspect ratios, and resolutions.
- **references/prompting_tips.md**: Best practices for cinematic prompting and advanced workflows.
