from flask import Flask, request, jsonify, send_from_directory
import moviepy.editor as mp
from moviepy.video.fx.resize import resize
import os
import time
from flask_cors import CORS
import requests
import random
import re
import PIL
from PIL import Image
import numpy as np
from IPython.display import display
# moviepy.video.VideoClip.crossfade
app = Flask(__name__)
CORS(app)

def get_stoic_quotes(num_quotes):
    print(PIL.__version__)
    url = "https://stoic-quotes.com/api/quotes"
    response = requests.get(url)
    if response.status_code == 200:
        quotes = response.json()
        selected_quotes = random.sample(quotes, num_quotes)
        return [(quote['text'], quote['author']) for quote in selected_quotes]
    else:
        return []

def get_stoic_quotes_new(num_quotes):
    url = "https://stoic-quotes.com/api/quotes"
    response = requests.get(url)
    if response.status_code == 200:
        quotes = response.json()
        selected_quotes = random.sample(quotes, num_quotes)
        return selected_quotes
    else:
        return None

def text_to_speech(text, api_key, tts_voice_id):
    try:
        print(f"speech_file: {text}")
        VOICE_ID = tts_voice_id
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
        headers = {
            "Accept": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        response = requests.post(url, headers=headers, json=data, stream=True)
        if response.ok:
            timestamp = str(time.time()).replace('.', '')
            outfile = f"quote_3_{timestamp}.mp3"
            with open(outfile, 'wb') as f:
                f.write(response.content)
                print("Voiceover generated")
            return outfile
        else:
            return None
    except Exception as e:
        error_message = f'Error: {e}'
        print(error_message)
        return jsonify({'error': error_message}), 500

def random_sound_effect(sound_folder):
    sound_files = [f for f in os.listdir(sound_folder) if not f.startswith(".")]
    sound_file = random.choice(sound_files)
    return os.path.join(sound_folder, sound_file)

def random_image_(image_folder, used_images):
    image_files = [f for f in os.listdir(image_folder) if f not in used_images and not f.startswith('.')]
    if not image_files:
        return None
    image_file = random.choice(image_files)
    used_images.append(image_file)
    return os.path.join(image_folder, image_file)

def random_image__(image_folder, used_images):
    # Pixabay API parameters
    base_url = "https://pixabay.com/api/"
    api_key = "43817308-8703be08e4803d0a1ec6a2090"
    query = "stoicism"  # Example search term
    image_type = "photo"  # Filter by photo type
    per_page = 100  # Number of results per page

    # Construct the API request URL
    api_url = f"{base_url}?key={api_key}&q={query}&image_type={image_type}&per_page={per_page}"

    # Make the GET request to Pixabay API
    response = requests.get(api_url)
    data = response.json()

    # Extract image URLs from the response
    image_urls = [hit["webformatURL"] for hit in data.get("hits", [])]

    # Choose a random image URL from the list
    if not image_urls:
        return None
    image_url = random.choice(image_urls)

    # Optional: You can download the image using requests library if needed
    # response = requests.get(image_url)
    # with open("random_image.jpg", "wb") as f:
    #     f.write(response.content)

    return image_url

def random_image(image_folder, used_images):
    # Pixabay API parameters
    base_url = "https://pixabay.com/api/"
    api_key = "43817308-8703be08e4803d0a1ec6a2090"  # Replace with your own API key
    query = "stoicism"  # Example search term
    image_type = "photo"  # Filter by photo type
    per_page = 100  # Number of results per page

    # Construct the API request URL
    api_url = f"{base_url}?key={api_key}&q={query}&image_type={image_type}&per_page={per_page}&min_width=1080&min_height=1920"

    # Make the GET request to Pixabay API
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for unsuccessful requests
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

    data = response.json()

    # Extract image URLs from the response
    image_data = data.get("hits", [])
    if not image_data:
        print(f"No images found for query: {query}")
        return None

    # Choose a random image from the data
    random_image_info = random.choice(image_data)
    image_url = random_image_info["largeImageURL"]

    # Download the image and save it locally
    image_filename = os.path.join(image_folder, f"image_{time.time()}.jpg")
    try:
        # Download the image using requests.get with stream=True for efficiency
        image_response = requests.get(image_url, stream=True)
        image_response.raise_for_status()  # Raise an exception for download errors

        with open(image_filename, 'wb') as f:
            for chunk in image_response.iter_content(1024):
                f.write(chunk)
        return image_filename
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

def create_transition(clip, transition_type, duration):
    if transition_type == 'fade':
        return clip.fadein(duration).fadeout(duration)
    elif transition_type == 'slide':
        return clip.crossfadein(duration).crossfadeout(duration)
    else:
        return clip.fadein(duration).fadeout(duration)
    
def apply_black_noise(clip, duration):
    # Check if the input is a CompositeVideoClip
    if isinstance(clip, mp.CompositeVideoClip):
        # Convert the CompositeVideoClip to a regular VideoClip
        clip = clip.clips[0]

    # Generate black noise with the same shape as the clip frame
    noise = np.random.randint(0, 256, size=(clip.h, clip.w, 3), dtype=np.uint8)

    # Convert the clip to a grayscale color space
    grayscale_clip = clip.fl_image(lambda img: Image.fromarray(img).convert('L'))

    # Create a VideoClip from the noise array
    noise_clip = mp.ImageClip(noise).set_duration(duration)

    # Combine the grayscale clip with the noise clip as an overlay
    noisy_clip = mp.CompositeVideoClip([grayscale_clip, noise_clip], size=clip.size)

    # Adjust the opacity of the noise layer to control the intensity of the effect
    noisy_clip.set_opacity(0.3)  # Adjust opacity between 0 (invisible) and 1 (fully opaque)
    return noisy_clip

def get_quotes(limit):
    url = "https://dr-almotawa-quotes.p.rapidapi.com/getRandomQuote"
    querystring = {"limit":"50"}
    headers = {
        "X-RapidAPI-Key": "1e37dc205fmsha6035427a78df27p1e2e15jsnf96ce28bcda5",
        "X-RapidAPI-Host": "dr-almotawa-quotes.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    print(response.json())

@app.route('/generate-video-old', methods=['POST'])
def generate_video_old():
    try:
        data = request.get_json()
        print("Received data:", data)
        used_images = []
        font_size = data.get('font_size', 70)
        font_color = data.get('font_color', 'yellow')
        background_color = data.get('background_color', 'black')
        background_opacity = data.get('background_opacity', 1.0)
        tts_voice_id = data.get('tts_voice_id', "2EiwWnXFnvU5JabPnv8n")
        tts_api_key = data.get('tts_api_key', "33fea3ee4061b241d69e312ad7aa0ef1")

        num_quotes = data.get('num_quotes', 5)
        quotes = get_stoic_quotes(num_quotes)
        if not quotes:
            raise Exception("Failed to retrieve any stoic quotes from API")

        video_clips = []

        for quote, author in quotes:
            print(f"Quote: {quote}")
            speech_file = text_to_speech(quote, tts_api_key, tts_voice_id)
            if not speech_file:
                continue
            # Create an audio clip from the generated voiceover
            audio_clip = mp.AudioFileClip(speech_file)

            background_image_path = random_image('./images', used_images)
            if not background_image_path:
                continue

            # Split the quote into sentences
            sentences = quote.split('. ')
            sentence_clips = []
            for sentence in sentences:
                sentence_text = f"{sentence}. \n ~ {author} ~"
                sentence_clip = mp.TextClip(
                    sentence_text,
                    fontsize=font_size,
                    font="Futura-bold",
                    stroke_color="black",
                    stroke_width=2,
                    size=(1080, 0),
                    color=font_color,
                    method="caption",
                ).set_pos(('center')).set_duration(audio_clip.duration / len(sentences))
                 # Calculate the position to center the text vertically
                text_height = sentence_clip.h
                video_height = 1920
                bottom_distance = 100  # Adjust this value as needed
                center_y = (video_height - text_height) / 2
                sentence_clip = sentence_clip.set_position(('center', center_y - bottom_distance))

                sentence_clips.append(sentence_clip)

            # Concatenate the sentence clips
            text_clip = mp.concatenate_videoclips(sentence_clips)

            # Create the final composite clip
            bg_image = Image.open(background_image_path)
            bg_image = bg_image.resize((1080, 1920), Image.BILINEAR)
            bg_image = bg_image.convert('RGB')
            bg_image_clip = mp.ImageClip(np.array(bg_image)).set_duration(text_clip.duration)
            final_clip = mp.CompositeVideoClip([bg_image_clip, text_clip], size=(1080, 1920))
            
            transition_type = random.choice(['fade','slide','zoom'])
            final_clip = create_transition(final_clip, 'fade', 1.5)

            # Set the audio for the final clip
            final_clip = final_clip.set_audio(audio_clip) 
            video_clips.append(final_clip)

        print("Number of video clips:", len(video_clips))
        # Concatenate all video clips
        final_video = mp.concatenate_videoclips(video_clips)

        # Add gaps of silence between clips
        silence_duration = 0.6  # Adjust the duration of silence as needed
        silence_clip = mp.AudioFileClip("src/1-sec-300ms-silence.mp3").subclip(0, silence_duration)

        video_clips_with_silence = []
        for clip in video_clips:
            video_clips_with_silence.append(clip)
            video_clips_with_silence.append(mp.VideoFileClip("src/black.mp4").set_duration(silence_duration).set_audio(silence_clip))

        # Concatenate all video clips with silence
        final_video = mp.concatenate_videoclips(video_clips_with_silence)

        speed_factor = 0.8  # Adjust the speed factor as needed (0.8 means 80% of the original speed)
        final_video = final_video.fx(mp.vfx.speedx, factor=speed_factor)
        # Add watermark signature text
        watermark_text = "Stoic the Great."
        watermark_clip = mp.TextClip(watermark_text, fontsize=50, color='white', font="Futura-bold")
        watermark_clip = watermark_clip.set_pos(('right', 'bottom')).set_duration(final_video.duration)

        final_video = mp.CompositeVideoClip([final_video, watermark_clip])

        # Apply black noise effect
        # final_video = apply_black_noise(final_video, duration=final_video.duration)

        # Define the directory for saving the video file
        output_directory = 'VSL'
        os.makedirs(output_directory, exist_ok=True)

        # Add background sound effect
        sound_effect_path = random_sound_effect('./sounds')
        if sound_effect_path:
            sound_effect_clip = mp.AudioFileClip(sound_effect_path)
            if sound_effect_clip.duration < final_video.duration:
                # Loop the sound effect clip to match the duration of the final video
                sound_effect_clip = mp.afx.audio_loop(sound_effect_clip, duration=final_video.duration)
            else:
                sound_effect_clip = sound_effect_clip.subclip(0, final_video.duration)
            final_video = final_video.set_audio(mp.CompositeAudioClip([final_video.audio, sound_effect_clip]))
        timestamp = str(time.time()).replace('.', '')
        # Write the video file using moviepy
        video_output_path = os.path.join(output_directory, 'English-daily-quote-stoic-{timestamp}.mp4')
        final_video.fps = video_clips[0].fps if video_clips else 24  # Set fps of final_video to the fps of the first clip
        final_video.write_videofile(video_output_path, fps=24, codec='libx264', audio_codec='aac', bitrate='10M')
        print("Video generated")

        # Return the generated video file path
        return send_from_directory(output_directory, 'English-daily-quote-stoic-{timestamp}.mp4')

    except Exception as e:
        error_message = f'Error: {e}'
        print(error_message)
        return jsonify({'error': error_message}), 500

@app.route('/generate-video', methods=['POST'])
def generate_video():
    try:
        data = request.get_json()
        print("Received data:", data)
        used_images = []
        font_size = data.get('font_size', 70)
        font_color = data.get('font_color', 'yellow')
        background_color = data.get('background_color', 'black')
        background_opacity = data.get('background_opacity', 1.0)
        tts_voice_id = data.get('tts_voice_id', "2EiwWnXFnvU5JabPnv8n")
        tts_api_key = data.get('tts_api_key', "33fea3ee4061b241d69e312ad7aa0ef1")

        num_quotes = data.get('num_quotes', 3)
        quotes = get_stoic_quotes(num_quotes)
        if not quotes:
            raise Exception("Failed to retrieve any stoic quotes from API")

        video_clips = []

        for quote, author in quotes:
            print(f"Quote: {quote}")
            speech_file = text_to_speech(quote, tts_api_key, tts_voice_id)
            # open('quote_3_17153780724472399.mp3')
            if not speech_file:
                continue
            # Create an audio clip from the generated voiceover
            audio_clip = mp.AudioFileClip(speech_file)

            background_image_path = random_image('./images', used_images)
            if not background_image_path:
                continue

            # Split the quote into sentences
            sentences = quote.split('. ')
            sentence_clips = []
            for sentence in sentences:
                sentence_text = f"{sentence}. \n ~ {author} ~"
                sentence_clip = mp.TextClip(
                    sentence_text,
                    fontsize=font_size,
                    font="Futura-bold",
                    stroke_color="black",
                    stroke_width=2,
                    size=(1080, 0),
                    color=font_color,
                    method="caption",
                ).set_pos(('center','bottom')).set_duration(audio_clip.duration / len(sentences))
                
                # Calculate the position to center the text vertically
                text_height = sentence_clip.h
                video_height = 1920
                bottom_distance = 100  # Adjust this value as needed
                center_y = (video_height - text_height) / 2
                sentence_clip = sentence_clip.set_position(('center', center_y))

                sentence_clips.append(sentence_clip)

            # Concatenate the sentence clips
            text_clip = mp.concatenate_videoclips(sentence_clips)

            # Create the final composite clip
            bg_image = Image.open(background_image_path)
            bg_image = bg_image.resize((1080, 1920), Image.BILINEAR)
            bg_image = bg_image.convert('RGB')
            bg_image_clip = mp.ImageClip(np.array(bg_image)).set_duration(text_clip.duration)
            final_clip = mp.CompositeVideoClip([bg_image_clip, text_clip], size=(1080, 1920))
            
            transition_type = random.choice(['fade','slide','zoom'])
            final_clip = create_transition(final_clip, 'fade', 1.5)

            # Set the audio for the final clip
            final_clip = final_clip.set_audio(audio_clip) 
            video_clips.append(final_clip)

        print("Number of video clips:", len(video_clips))
        # Concatenate all video clips
        final_video = mp.concatenate_videoclips(video_clips)

        # Add gaps of silence between clips
        silence_duration = 0.6  # Adjust the duration of silence as needed
        silence_clip = mp.AudioFileClip("src/1-sec-300ms-silence.mp3").subclip(0, silence_duration)

        video_clips_with_silence = []
        for clip in video_clips:
            video_clips_with_silence.append(clip)
            video_clips_with_silence.append(mp.VideoFileClip("src/black.mp4").set_duration(silence_duration).set_audio(silence_clip))

        # Concatenate all video clips with silence
        final_video = mp.concatenate_videoclips(video_clips_with_silence)

        speed_factor = 0.8  # Adjust the speed factor as needed (0.8 means 80% of the original speed)
        final_video = final_video.fx(mp.vfx.speedx, factor=speed_factor)
        # Add watermark signature text
        watermark_text = "Stoic the Great."
        watermark_clip = mp.TextClip(watermark_text, fontsize=50, color='white', font="Futura-bold")
        watermark_clip = watermark_clip.set_pos(('right', 'bottom')).set_duration(final_video.duration)

        final_video = mp.CompositeVideoClip([final_video, watermark_clip])

        # Define the directory for saving the video file
        output_directory = 'VSL'
        os.makedirs(output_directory, exist_ok=True)

        # Add background sound effect
        sound_effect_path = random_sound_effect('./sounds')
        if sound_effect_path:
            sound_effect_clip = mp.AudioFileClip(sound_effect_path)
            if sound_effect_clip.duration < final_video.duration:
                # Loop the sound effect clip to match the duration of the final video
                sound_effect_clip = mp.afx.audio_loop(sound_effect_clip, duration=final_video.duration)
            else:
                sound_effect_clip = sound_effect_clip.subclip(0, final_video.duration)
            final_video = final_video.set_audio(mp.CompositeAudioClip([final_video.audio, sound_effect_clip]))
        timestamp = str(time.time()).replace('.', '')
        # Write the video file using moviepy
        video_output_path = os.path.join(output_directory, f'English-daily-quote-stoic-{timestamp}.mp4')
        final_video.fps = video_clips[0].fps if video_clips else 24  # Set fps of final_video to the fps of the first clip
        final_video.write_videofile(video_output_path, fps=24, codec='libx264', audio_codec='aac', bitrate='10M')
        print("Video generated")

        # Return the generated video file path
        return send_from_directory(output_directory, f'English-daily-quote-stoic-{timestamp}.mp4')

    except Exception as e:
        error_message = f'Error: {e}'
        print(error_message)
        return jsonify({'error': error_message}), 500
                         
if __name__ == '__main__':
    app.run(debug=True)