# Gemini Image Generation API Reference

Technical specifications for Gemini 2.5 Flash and Gemini 3 Pro image models.

## Models

| Model Name | Internal Name | Description |
|---|---|---|
| **Gemini 2.5 Flash** | `gemini-2.5-flash-image` | High-speed image generation and processing. |
| **Gemini 3 Pro** | `gemini-3-pro-image-preview` | Professional-grade asset production, 4K support, reasoning. |

## Capabilities

- **Text-to-Image**: Generate from descriptive prompts.
- **Image-to-Image**: Edit existing images via text prompts (add/remove/modify).
- **Multi-turn Editing**: Refine images conversationally in a chat.
- **Text Rendering**: High-fidelity legible text for logo/menus/diagrams.
- **Grounding (3 Pro only)**: Use Google Search for factual accuracy in imagery.

## Technical Parameters

### Aspect Ratios
Supported values: `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`, `"21:9"`.

### Resolution (3 Pro only)
Supported values: `"1K"`, `"2K"`, `"4K"`.

### Multi-image Input (3 Pro only)
- Up to **14 reference images** total.
- Up to **6 object images** for high-fidelity inclusion.
- Up to **5 human images** for character consistency.

## Usage Patterns

### Basic Generation (Python)
```python
client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
)
```

### Editing with Image Config (Python)
```python
client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[prompt, image],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        ),
    )
)
```

## Responsible AI
- All images include **SynthID watermarks**.
- Prohibited from generating harmful, harassing, or infringing content.
