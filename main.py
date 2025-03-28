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
    
    def monitor_and_download(self, task_id, output_path, max_checks=30, check_interval=10):
        """
        Monitor a task until completion and download the result.
        
        Args:
            task_id: Task ID to monitor
            output_path: Where to save the downloaded file
            max_checks: Maximum number of status checks
            check_interval: Seconds between checks
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Monitoring task ID: {task_id}")
        print(f"Will save to: {output_path}")
        
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
                
                if api_code == 429:
                    print("Insufficient credits. Please add more credits to your account.")
                elif api_code == 455:
                    print("System is under maintenance. Please try again later.")
                
                # For most errors, we should stop polling
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
                    success = self.download_music(audio_url, output_path)
                    return success
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
    
    args = parser.parse_args()
    
    # Check for API keys first
    if not os.getenv("SUNO_API_KEY"):
        print("ERROR: SUNO_API_KEY environment variable is not set.")
        print("Please add your Suno API key to the .env file.")
        return
    
    if not args.instrumental and not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please add your Anthropic API key to the .env file or use --instrumental flag.")
        return
    
    # Create music generator instance
    music_gen = MusicGenerator(debug=args.debug)
    
    # If checking an existing task
    if args.check_task:
        task_id = args.check_task
        
        # If no task ID provided but --check-task flag is used, try to read from file
        if task_id == True:
            try:
                with open('last_task_id.txt', 'r') as f:
                    task_id = f.read().strip()
                print(f"Using task ID from last_task_id.txt: {task_id}")
            except FileNotFoundError:
                print("No task ID provided and no last_task_id.txt file found.")
                return
        
        print(f"Checking existing task: {task_id}")
        music_gen.monitor_and_download(task_id, args.output, args.checks, args.interval)
        return
    
    # Ensure theme is provided for new music generation
    if not args.theme:
        print("Please provide a theme with --theme")
        return
    
    # Generate lyrics using Anthropic (skip if instrumental is requested)
    lyrics_content = ""
    lyrics_title = ""
    
    if not args.instrumental:
        print(f"Generating lyrics about '{args.theme}' in {args.style} style...")
        lyrics_gen = LyricsGenerator()
        lyrics_result = lyrics_gen.generate_lyrics(
            args.theme, 
            style=args.style,
            num_verses=args.verses,
            has_chorus=args.chorus
        )
        
        lyrics_title = lyrics_result['title']
        lyrics_content = lyrics_result['content']
        
        print(f"\nGenerated title: {lyrics_title}")
        print("Generated lyrics:")
        print("-" * 40)
        print(lyrics_content)
        print("-" * 40)
    else:
        # If instrumental, just use the theme as prompt
        lyrics_content = args.theme
        lyrics_title = args.theme.capitalize()
        print(f"Creating instrumental music with theme: {args.theme}")
    
    # Generate music using Suno API
    print("\nGenerating music with Suno API...")
    generation_response = music_gen.generate_music(
        lyrics_title,
        lyrics_content,
        args.style,
        custom_mode=args.custom,
        instrumental=args.instrumental,
        model=args.model
    )
    
    if not generation_response:
        print("Failed to start music generation. Please check the error messages above.")
        return
    
    if args.debug:
        print("Full API response:")
        print(json.dumps(generation_response, indent=2))
    
    # Check for the task ID in the response
    task_id = None
    try:
        task_id = generation_response.get('data', {}).get('taskId')
        if not task_id:
            # Try alternative paths for task ID
            task_id = generation_response.get('taskId')
            
            if not task_id:
                # Search for taskId recursively
                def find_task_id(obj):
                    if isinstance(obj, dict):
                        if 'taskId' in obj:
                            return obj['taskId']
                        for k, v in obj.items():
                            result = find_task_id(v)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for item in obj:
                            result = find_task_id(item)
                            if result:
                                return result
                    return None
                
                task_id = find_task_id(generation_response)
    except (KeyError, TypeError, AttributeError) as e:
        print(f"Error extracting task ID: {e}")
        print("API Response structure:")
        print(json.dumps(generation_response, indent=2))
        return
    
    if not task_id:
        print("No task ID returned from Suno API.")
        print("API Response structure:")
        print(json.dumps(generation_response, indent=2))
        return
    
    print(f"Music generation started with task ID: {task_id}")
    
    # Monitor the task until completion and download
    music_gen.monitor_and_download(task_id, args.output, args.checks, args.interval)


if __name__ == "__main__":
    main()
