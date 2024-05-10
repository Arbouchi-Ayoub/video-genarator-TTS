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

def text_to_speech(text, api_key):
    try:
        print(f"speech_file: {text}")
        VOICE_ID = ""
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

def random_image(image_folder, used_images):
    image_files = [f for f in os.listdir(image_folder) if f not in used_images and not f.startswith('.')]
    if not image_files:
        return None
    image_file = random.choice(image_files)
    used_images.append(image_file)
    return os.path.join(image_folder, image_file)

@app.route('/generate-video', methods=['POST'])
def generate_video():
    try:
        data = request.get_json()
        print("Received data:", data)
        used_images = []
        font_size = data.get('font_size', 70)
        font_color = data.get('font_color', 'white')
        background_color = data.get('background_color', 'black')
        background_opacity = data.get('background_opacity', 1.0)
        tts_api_key = data.get('tts_api_key', "API_KEY")

        num_quotes = data.get('num_quotes', 3)
        quotes = get_stoic_quotes(num_quotes)
        if not quotes:
            raise Exception("Failed to retrieve any stoic quotes from API")
        
        video_clips = []

        for quote, author in quotes:
            print(f"Quote: {quote}")
            speech_file = text_to_speech(quote, "API_KEY")
            if not speech_file:
                continue
            # Create an audio clip from the generated voiceover
            audio_clip = mp.AudioFileClip(speech_file)

            background_image_path = random_image('./images', used_images)
            if not background_image_path:
                continue

            # Create a single TextClip for the entire quote
            text_clip = mp.TextClip(
                f"{quote}\n ~ {author} ~",
                fontsize=font_size,
                font="Futura-bold",
                stroke_color="black",
                stroke_width=2,
                size=(900, 0),
                color=font_color,
                method="caption",
                # bg_color=background_color
            ).set_pos(('center')).set_duration(audio_clip.duration)

            # bg_color=background_color
            # Create the final composite clip
            bg_image = Image.open(background_image_path)
            bg_image = bg_image.resize((1500, 1000), Image.BILINEAR)
            bg_image = bg_image.convert('RGB')
            bg_image_clip = mp.ImageClip(np.array(bg_image)).set_duration(text_clip.duration)
            final_clip = mp.CompositeVideoClip([bg_image_clip, text_clip], size=(1500, 1000)) 
            
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

        speed_factor = 0.9  # Adjust the speed factor as needed (0.8 means 80% of the original speed)
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
        # Write the video file using moviepy
        video_output_path = os.path.join(output_directory, 'daily-quote-stoic-3.mp4')
        final_video.fps = video_clips[0].fps if video_clips else 24  # Set fps of final_video to the fps of the first clip
        final_video.write_videofile(video_output_path, fps=24, codec='libx264', audio_codec='aac')
        print("Video generated")

        # Return the generated video file path
        return send_from_directory(output_directory, 'daily-quote-stoic-3.mp4')

    except Exception as e:
        error_message = f'Error: {e}'
        print(error_message)
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)