# AI Time Capsule Project

This project is an AI-driven application that generates music and accompanying images based on user-defined themes. The application utilizes the OpenAI DALL-E API for image generation and the Suno API for music creation.

## Features
- **Music Generation**: Create music tracks based on themes and styles using the Suno API.
- **Image Generation**: Generate images that visually represent the theme using OpenAI's DALL-E.
- **Artifact Organization**: Each generation creates a dedicated folder containing both the audio and images.

## Usage
To run the application, use the following command:

```bash
python main.py --theme "your_theme" --style "your_style" --verses 2 --chorus --model "V3_5" --output "your_output.mp3" --debug --checks 40 --interval 15
```

### Command-Line Arguments
- `--theme`: The theme or idea for the song (required).
- `--style`: The music style (e.g., rock, pop, rap).
- `--verses`: Number of verses in the song.
- `--chorus`: Include a chorus in the song.
- `--model`: Model version to use for music generation.
- `--output`: Output file path for the generated audio.
- `--debug`: Enable debug output.
- `--checks`: Maximum number of status checks.
- `--interval`: Seconds between status checks.
- `--skip-images`: Skip image generation.

### Feature Descriptions
- **Theme**: Defines the central concept or idea around which the song and images are created.
- **Style**: Specifies the musical style, influencing the mood and instrumentation of the generated music.
- **Verses**: Determines how many verses the song will have, affecting its length and structure.
- **Chorus**: Adds a repetitive section to the song, enhancing its catchiness and structure.
- **Model**: Selects the version of the Suno API model to use, which can affect the quality and characteristics of the music.
- **Output**: Specifies where the generated audio file will be saved.
- **Debug**: Provides detailed output for troubleshooting and understanding the generation process.
- **Checks**: Limits the number of times the application will check the status of music generation, preventing infinite loops.
- **Interval**: Sets the time between status checks, balancing responsiveness and API load.
- **Skip Images**: Allows users to bypass image generation if only audio is desired.

## Example Prompts
- **Theme**: "Mystical Forest"
  - **Style**: "Cinematic"
  - **Command**: `python main.py --theme "Mystical Forest" --style "Cinematic" --verses 2 --chorus --model "V3_5" --output "mystical_forest.mp3"`

- **Theme**: "Galactic Odyssey"
  - **Style**: "Electronic"
  - **Command**: `python main.py --theme "Galactic Odyssey" --style "Electronic" --verses 2 --chorus --model "V3_5" --output "galactic_odyssey.mp3"`

## Requirements
- Python 3.x
- OpenAI API Key (for DALL-E)
- Suno API Key

Ensure that the `.env` file contains valid API keys for both OpenAI and Suno.

## Setup
1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application with your desired theme and style.

## Note
The `artifacts` directory is included in `.gitignore` to prevent generated content from being tracked in version control.
