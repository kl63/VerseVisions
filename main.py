#!/usr/bin/env python3
"""
Lyrics and Music Generator using Anthropic for lyrics and Suno API for music generation.
"""
import os
import json
import time
import argparse
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")
VIDEO_API_KEY = os.getenv("VIDEO_API_KEY")
DALLE_API_KEY = os.getenv("DALLE_API_KEY")

# API endpoints
SUNO_API_BASE_URL = "https://apibox.erweima.ai/api/v1"

# Suno API Status Codes
SUNO_STATUS = {
    "PENDING": "Pending execution",
    "TEXT_SUCCESS": "Text generation successful",
    "FIRST_SUCCESS": "First song generation successful",
    "SUCCESS": "Generation successful",
    "CREATE_TASK_FAILED": "Task creation failed",
    "GENERATE_AUDIO_FAILED": "Song generation failed",
    "CALLBACK_EXCEPTION": "Callback exception",
    "SENSITIVE_WORD_ERROR": "Sensitive word error"
}

class LyricsGenerator:
    """Class to generate lyrics using Anthropic's Claude model."""
    
    def __init__(self):
        """Initialize the Anthropic client."""
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def generate_lyrics(self, prompt, style=None, num_verses=2, has_chorus=True):
        """
        Generate lyrics using Anthropic's Claude model.
        
        Args:
            prompt: The main theme or idea for the lyrics
            style: Music style (e.g., "rock", "pop", "rap")
            num_verses: Number of verses to generate
            has_chorus: Whether to include a chorus
            
        Returns:
            dict: Generated lyrics with title and content
        """
        # Construct a detailed prompt for Claude
        system_prompt = """You are a professional songwriter with expertise in many musical styles.
        Create original, creative, and emotionally resonant lyrics that feel authentic to the requested style.
        Structure the lyrics properly and ensure they have a cohesive theme."""
        
        style_instruction = f"Write in {style} style. " if style else ""
        structure_instruction = f"Include {num_verses} verses"
        structure_instruction += " and a chorus that repeats." if has_chorus else "."
        
        user_prompt = f"{style_instruction}Write lyrics for a song about: {prompt}. {structure_instruction} \
        Include a title at the top. Format the output so verses and chorus are clearly separated."
        
        # Get response from Claude
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract lyrics and title
        lyrics_text = response.content[0].text
        
        # Parse out the title (assuming it's the first line)
        lines = lyrics_text.strip().split('\n')
        title = lines[0].replace("#", "").strip()
        content = '\n'.join(lines[1:]).strip()
        
        return {
            "title": title,
            "content": content,
            "full_text": lyrics_text
        }


class MusicGenerator:
    """Class to generate music using Suno API with lyrics."""
    
    def __init__(self, debug=False):
        """
        Initialize with the Suno API key.
        
        Args:
            debug: Enable detailed logging
        """
        self.api_key = SUNO_API_KEY
        self.debug = debug
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Verify API key is set
        if not self.api_key or self.api_key.strip() == "":
            print("ERROR: SUNO_API_KEY environment variable is not set or is empty.")
            print("Please add your Suno API key to the .env file.")

        # Video generation API setup
        self.video_api_key = VIDEO_API_KEY
        if not self.video_api_key or self.video_api_key.strip() == "":
            print("WARNING: VIDEO_API_KEY environment variable is not set or is empty.")
            print("Video generation will be skipped. Add your Video API key to the .env file to enable video generation.")
            self.video_enabled = False
        else:
            self.video_enabled = True

        # DALL-E API setup
        self.dalle_api_key = DALLE_API_KEY
        if not self.dalle_api_key or self.dalle_api_key.strip() == "":
            print("WARNING: DALLE_API_KEY environment variable is not set or is empty.")
            print("Image generation will be skipped. Add your DALL-E API key to the .env file to enable image generation.")
            self.dalle_enabled = False
        else:
            self.dalle_enabled = True

    def generate_music(self, title, lyrics, style, custom_mode=True, instrumental=False, model="V3_5"):
        """
        Generate music with lyrics using Suno API.
        
        Args:
            title: Song title
            lyrics: Lyrics content
            style: Music style description
            custom_mode: Whether to use custom mode (True) or non-custom mode (False)
            instrumental: Whether to generate instrumental music (no lyrics)
            model: Model version to use (V3_5 or V4)
            
        Returns:
            dict: Response from Suno API containing task ID and other details
        """
        # Truncate title if it exceeds 80 characters
        if len(title) > 80:
            print(f"Title is too long, truncating to 80 characters.")
            title = title[:80]
        
        # Prepare request payload
        payload = {
            "prompt": lyrics,
            "style": style if custom_mode else "",
            "title": title if custom_mode else "",
            "customMode": custom_mode,
            "instrumental": instrumental,
            "model": model,
            "callBackUrl": "https://example.com/callback"  # Placeholder, won't be used
        }
        
        # Log request for debugging
        print(f"Sending request to Suno API: {json.dumps(payload, indent=2)}")
        print(f"API URL: {SUNO_API_BASE_URL}/generate")
        
        # Make API request to generate audio
        try:
            response = requests.post(
                f"{SUNO_API_BASE_URL}/generate",
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout to prevent hanging
            )
            
            # Check for successful response
            if response.status_code == 200:
                resp_json = response.json()
                if self.debug:
                    print(f"API Response: {json.dumps(resp_json, indent=2)}")

                # Extract task ID
                task_id = resp_json.get('data', {}).get('taskId')
                if not task_id:
                    print("Error: Task ID not found in response.")
                    print(f"Full response: {json.dumps(resp_json, indent=2)}")
                    return None

                return resp_json
            else:
                print(f"Error generating music: Status code {response.status_code}")
                print(f"Response: {response.text}")
                
                # Try to parse as JSON to provide better error info
                try:
                    error_data = response.json()
                    if 'code' in error_data and 'msg' in error_data:
                        print(f"API Error Code: {error_data['code']}")
                        print(f"Error Message: {error_data['msg']}")
                        
                        if error_data['code'] == 401:
                            print("Authentication failed. Please check your API key.")
                        elif error_data['code'] == 429:
                            print("Insufficient credits. Please add credits to your account.")
                        elif error_data['code'] == 413:
                            print("Theme or prompt too long. Please use a shorter theme or lyrics.")
                except:
                    pass  # Ignore if not JSON
                
                return None
        except requests.exceptions.RequestException as e:
            print(f"Network error when contacting Suno API: {e}")
            return None

    def generate_video(self, title, lyrics, audio_path):
        """
        Generate a video using DeepAI video generation API.
        
        Args:
            title: Song title
            lyrics: Lyrics content
            audio_path: Path to the generated audio file
            
        Returns:
            str: URL of the generated video
        """
        # Verify that video generation is enabled and the audio file exists
        if not self.video_enabled:
            print("Skipping video generation as VIDEO_API_KEY is not set.")
            return None
            
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            print(f"Audio file not found or empty: {audio_path}")
            print("Skipping video generation.")
            return None
            
        print(f"Generating video for '{title}' using the audio file: {audio_path}")
        
        # DeepAI API endpoint
        video_api_url = "https://api.deepai.org/api/video-generator"
        
        # Create payload for video generation API
        payload = {
            "title": title,
            "text": lyrics
        }
        
        headers = {
            "api-key": self.video_api_key
        }
        
        try:
            print("Sending request to DeepAI video generation API...")
            if self.debug:
                print(f"Video API URL: {video_api_url}")
                print(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Attempt to generate video
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'audio': audio_file
                }
                response = requests.post(
                    video_api_url,
                    headers=headers,
                    data=payload,
                    files=files,
                    timeout=60  # Longer timeout for video generation
                )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    video_data = response.json()
                    print(f"Video generation response received.")
                    if self.debug:
                        print(f"Response data: {json.dumps(video_data, indent=2)}")
                    
                    # Extract video URL from response
                    video_url = video_data.get("output_url")
                    if video_url:
                        print(f"Video URL: {video_url}")
                        return video_url
                    else:
                        print("No video URL found in the response.")
                        if self.debug:
                            print(f"Full response: {json.dumps(video_data, indent=2)}")
                        return None
                except ValueError:
                    print("Invalid JSON response from video API.")
                    print(f"Raw response: {response.text[:200]}...")
                    return None
            else:
                print(f"Error generating video: Status code {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error during video generation: {e}")
            return None

    def generate_images_with_dalle(self, prompt, num_images=5):
        """
        Generate a series of images using OpenAI's DALL-E.
        
        Args:
            prompt: Text prompt to generate images
            num_images: Number of images to generate
            
        Returns:
            List of file paths to the generated images
        """
        import time
        import os

        # Create a directory for the prompt
        prompt_dir = os.path.join("artifacts", prompt.replace(" ", "_"))
        os.makedirs(prompt_dir, exist_ok=True)

        image_paths = []
        headers = {
            "Authorization": f"Bearer {self.dalle_api_key}"
        }
        
        for i in range(num_images):
            try:
                response = requests.post(
                    "https://api.openai.com/v1/images/generations",
                    headers=headers,
                    json={"prompt": prompt, "n": 1, "size": "1024x1024"}
                )
                
                if response.status_code == 200:
                    image_data = response.json()
                    image_url = image_data['data'][0]['url']
                    image_path = self.download_image(image_url, os.path.join(prompt_dir, f"image_{i+1}.png"))
                    image_paths.append(image_path)
                else:
                    print(f"Error generating image {i+1}: {response.status_code}")
                
                # Add delay to prevent hitting rate limits
                time.sleep(2)
            except Exception as e:
                print(f"Exception occurred while generating image {i+1}: {e}")
        
        return image_paths

    def download_image(self, url, output_path):
        """
        Download an image from a URL to a local file.
        
        Args:
            url: URL of the image to download
            output_path: Path where to save the downloaded image
        """
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Image downloaded successfully: {output_path}")
                return output_path
            else:
                print(f"Failed to download image: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Network error while downloading image: {e}")
            return None

    def find_audio_url(self, obj):
        """
        Recursively search for audio URL in a nested JSON object.
        
        Args:
            obj: JSON object to search
            
        Returns:
            str: Audio URL if found, None otherwise
        """
        if isinstance(obj, dict):
            # Direct field matches
            for key in ['audioUrl', 'audio_url', 'url', 'mp3Url', 'streamUrl']:
                if key in obj and isinstance(obj[key], str) and (
                        obj[key].startswith('http') and 
                        ('.mp3' in obj[key] or '.wav' in obj[key] or '/audio/' in obj[key])
                    ):
                    return obj[key]
            
            # Search recursively in all values
            for k, v in obj.items():
                result = self.find_audio_url(v)
                if result:
                    return result
        
        elif isinstance(obj, list):
            for item in obj:
                result = self.find_audio_url(item)
                if result:
                    return result
        
        return None
    
    def check_generation_status(self, task_id):
        """
        Check the status of a generation task.
        
        Args:
            task_id: The task ID returned from generate_music
            
        Returns:
            dict: Task details including status and results if available
        """
        # The primary endpoint according to documentation
        primary_endpoint = f"{SUNO_API_BASE_URL}/generate/record-info?taskId={task_id}"
        print(f"Checking status at: {primary_endpoint}")
        
        try:
            response = requests.get(primary_endpoint, headers=self.headers, timeout=30)
            if response.status_code == 200:
                print("Status check successful")
                return response.json()
            
            # If primary endpoint fails, try these alternative endpoints
            alternate_endpoints = [
                f"{SUNO_API_BASE_URL}/generate/status?taskId={task_id}",
                f"{SUNO_API_BASE_URL}/generate/result?taskId={task_id}",
                f"{SUNO_API_BASE_URL}/task/{task_id}",
                f"{SUNO_API_BASE_URL}/generate/{task_id}"
            ]
            
            for endpoint in alternate_endpoints:
                print(f"Primary endpoint failed, trying: {endpoint}")
                alt_response = requests.get(endpoint, headers=self.headers, timeout=30)
                
                if alt_response.status_code == 200:
                    print(f"Success with alternate endpoint: {endpoint}")
                    return alt_response.json()
            
            print("All endpoints failed for status check")
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"Network error when checking status: {e}")
            return None
    
    def get_status_description(self, status_code):
        """
        Get a human-readable description of a status code.
        
        Args:
            status_code: Status code from the API
            
        Returns:
            str: Human-readable description
        """
        return SUNO_STATUS.get(status_code, f"Unknown status: {status_code}")
    
    def download_music(self, audio_url, output_path, max_retries=5):
        """
        Download the generated music to a local file with retry mechanism.
        
        Args:
            audio_url: URL to the generated audio
            output_path: Path where to save the downloaded file
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                print(f"Download attempt {retry_count + 1}/{max_retries} from {audio_url}")
                
                # Try with streaming (better for large files)
                with requests.get(audio_url, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    
                    # Get file size if available
                    file_size = int(response.headers.get('content-length', 0))
                    if file_size:
                        print(f"File size: {file_size / 1024 / 1024:.2f} MB")
                    
                    # Download with progress tracking
                    with open(output_path, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if file_size:
                                    progress = (downloaded / file_size) * 100
                                    print(f"\rProgress: {progress:.1f}%", end='')
                    print("\nDownload complete!")
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        print(f"File saved to {output_path}")
                        return True
                    else:
                        print("Downloaded file is empty. Retrying...")
                
            except Exception as e:
                print(f"Download error: {e}")
            
            # Increase wait time between retries
            wait_time = 2 ** retry_count
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retry_count += 1
        
        return False
    
    def monitor_and_download(self, task_id, output_path, title="", lyrics="", max_checks=30, check_interval=10):
        """
        Monitor a task until completion and download the result.
        
        Args:
            task_id: Task ID to monitor
            output_path: Where to save the downloaded file
            title: Song title (for video generation)
            lyrics: Song lyrics (for video generation)
            max_checks: Maximum number of status checks
            check_interval: Seconds between checks
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Monitoring task ID: {task_id}")
        print(f"Will save audio to: {output_path}")
        
        # Save task ID to a file for later use if needed
        with open('last_task_id.txt', 'w') as f:
            f.write(task_id)
        print(f"Task ID saved to last_task_id.txt")
        
        checks = 0
        while checks < max_checks:
            print(f"\nCheck {checks + 1}/{max_checks}...")
            
            task_details = self.check_generation_status(task_id)
            if not task_details:
                print("Could not retrieve task details, waiting before retry...")
                time.sleep(check_interval)
                checks += 1
                continue
            
            # Check if we have an error in the API response
            api_code = task_details.get('code')
            if api_code and api_code != 200:
                error_msg = task_details.get('msg', 'Unknown error')
                print(f"API error: {api_code} - {error_msg}")
                
                if api_code not in [200, 404]:  # 404 might be temporary
                    return False
            
            # For proper error handling, first check the data object
            data = task_details.get('data', {})
            
            # Try to extract status using the documented path
            status = None
            if isinstance(data, dict):
                status = data.get('status')
            
            # If status is not in data, try alternative paths
            if not status:
                status = task_details.get('status')
                
                if not status:
                    # Search recursively if needed
                    def find_status(obj):
                        if isinstance(obj, dict):
                            if 'status' in obj:
                                return obj['status']
                            for k, v in obj.items():
                                result = find_status(v)
                                if result:
                                    return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = find_status(item)
                                if result:
                                    return result
                        return None
                    
                    status = find_status(task_details)
            
            status_desc = self.get_status_description(status)
            print(f"Current status: {status} - {status_desc}")
            
            # When debugging, show the full response
            if self.debug:
                print("Full API response:")
                print(json.dumps(task_details, indent=2))
            
            # Check for completion based on documented status codes
            if status == 'SUCCESS' or status == 'FIRST_SUCCESS':
                print("Task is complete!")
                
                # Find audio URL
                audio_url = self.find_audio_url(task_details)
                
                if audio_url:
                    print(f"Found audio URL: {audio_url}")
                    audio_success = self.download_music(audio_url, output_path)
                    
                    if audio_success and self.dalle_enabled and title:
                        # Now that audio is downloaded, generate images
                        print("\n=== Starting Image Generation ===")
                        image_paths = self.generate_images_with_dalle(title)
                        if image_paths:
                            print("Images generated successfully.")
                        return audio_success
                    else:
                        print("Image generation failed or not available, but audio was successful.")
                    
                    return audio_success
                else:
                    print("No audio URL found in the response.")
            
            elif status in ['CREATE_TASK_FAILED', 'GENERATE_AUDIO_FAILED', 'CALLBACK_EXCEPTION', 'SENSITIVE_WORD_ERROR']:
                print(f"Task failed: {status_desc}")
                return False
            
            elif status in ['PENDING', 'TEXT_SUCCESS']:
                print(f"Task still processing ({status_desc}). Checking again in {check_interval} seconds...")
            
            checks += 1
            time.sleep(check_interval)
        
        print("Exceeded maximum checks. Task may still be processing.")
        print(f"You can check again later using: python main.py --check-task {task_id} --output {output_path}")
        return False

    def create_video_from_images_and_lyrics(self, image_paths, lyrics, output_video_path, audio_path):
        """
        Create a video from a series of images with lyrics overlaid as text and add audio.
        
        Args:
            image_paths: List of file paths to the images
            lyrics: Lyrics to overlay on the video
            output_video_path: Path to save the generated video
            audio_path: Path to the audio file to include in the video
        """
        from moviepy.editor import ImageClip, concatenate_videoclips, TextClip, CompositeVideoClip, AudioFileClip
        
        # Create video clips from images
        clips = []
        for image_path in image_paths:
            clip = ImageClip(image_path).set_duration(3)  # Each image lasts 3 seconds
            clips.append(clip)
        
        # Concatenate image clips
        video = concatenate_videoclips(clips, method="compose")
        
        # Create a text clip for lyrics
        text_clip = TextClip(lyrics, fontsize=24, color='white', bg_color='black', size=video.size)
        text_clip = text_clip.set_duration(video.duration).set_position(('center', 'bottom'))
        
        # Overlay text on video
        final_video = CompositeVideoClip([video, text_clip])

        # Add audio to the video
        audio = AudioFileClip(audio_path)
        final_video = final_video.set_audio(audio)
        
        # Write the video file
        final_video.write_videofile(output_video_path, fps=24)
        print(f"Video created successfully: {output_video_path}")


def main():
    """Main function to orchestrate lyrics and music generation."""
    parser = argparse.ArgumentParser(description='Generate lyrics and music')
    parser.add_argument('--theme', type=str, help='Theme or idea for the song')
    parser.add_argument('--style', type=str, default='pop', help='Music style (e.g., rock, pop, rap)')
    parser.add_argument('--verses', type=int, default=2, help='Number of verses')
    parser.add_argument('--chorus', action='store_true', help='Include a chorus')
    parser.add_argument('--custom', action='store_true', default=True, help='Use custom mode for Suno API')
    parser.add_argument('--instrumental', action='store_true', help='Generate instrumental music (no lyrics)')
    parser.add_argument('--model', type=str, default='V3_5', choices=['V3_5', 'V4'], help='Suno API model to use')
    parser.add_argument('--output', type=str, default='output.mp3', help='Output file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--checks', type=int, default=30, help='Maximum number of status checks')
    parser.add_argument('--interval', type=int, default=10, help='Seconds between status checks')
    parser.add_argument('--check-task', type=str, nargs='?', const=True, help='Check status of an existing task ID and download the result')
    parser.add_argument('--skip-images', action='store_true', help='Skip image generation even if DALLE_API_KEY is set')
    
    args = parser.parse_args()
    
    # Create music generator instance
    music_gen = MusicGenerator(debug=args.debug)
    
    # Disable image generation if requested
    if args.skip_images:
        music_gen.dalle_enabled = False
        print("Image generation disabled by command line argument.")
    
    # If checking an existing task
    if args.check_task:
        task_id = args.check_task
        if not os.path.exists(args.output):
            print(f"Output file not found: {args.output}")
            return
        
        print(f"Checking existing task: {task_id}")
        music_gen.monitor_and_download(task_id, args.output)
        return
    
    # Ensure theme is provided for new music generation
    if not args.theme:
        print("ERROR: Theme is required for music generation.")
        return
    
    # Generate lyrics
    lyrics_gen = LyricsGenerator()
    lyrics_response = lyrics_gen.generate_lyrics(args.theme, args.style, args.verses, args.chorus)
    lyrics_title = lyrics_response['title']
    lyrics_content = lyrics_response['content']
    
    # Create a directory for the prompt
    prompt_dir = os.path.join("artifacts", args.theme.replace(" ", "_"))
    os.makedirs(prompt_dir, exist_ok=True)
    
    # Generate music
    music_gen_response = music_gen.generate_music(lyrics_title, lyrics_content, args.style, args.custom, args.instrumental, args.model)
    task_id = music_gen_response.get('data', {}).get('taskId')
    if not task_id:
        print("Error: Task ID not found in response.")
        print(f"Full response: {json.dumps(music_gen_response, indent=2)}")
        return
    print(f"Music generation started with task ID: {task_id}")
    
    # Monitor the task until completion and download
    audio_success = music_gen.monitor_and_download(
        task_id, 
        os.path.join(prompt_dir, args.output), 
        title=lyrics_title,
        lyrics=lyrics_content,
        max_checks=args.checks, 
        check_interval=args.interval
    )
    
    # Generate images if audio was successful
    if audio_success and not args.skip_images:
        print("\n=== Starting Image Generation ===")
        image_paths = music_gen.generate_images_with_dalle(lyrics_title)
        if image_paths:
            print("Images generated successfully.")
        return  # End the application after image generation


if __name__ == "__main__":
    main()