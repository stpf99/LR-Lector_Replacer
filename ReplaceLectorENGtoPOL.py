import subprocess
import os
from pydub import AudioSegment
import pysrt
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from moviepy.editor import VideoFileClip, AudioFileClip
from deep_translator import GoogleTranslator

class AudioSubGenerator(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Lector_Replacer")
        self.set_border_width(10)
        self.set_default_size(400, 300)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Target language
        target_language_box = Gtk.Box(spacing=6)
        vbox.pack_start(target_language_box, False, False, 0)
        target_language_label = Gtk.Label(label="Subtitles Target Language:")
        target_language_box.pack_start(target_language_label, False, False, 0)
        self.target_language_entry = Gtk.Entry()
        self.target_language_entry.set_text("pl")
        target_language_box.pack_start(self.target_language_entry, True, True, 0)

        # Input file
        input_file_box = Gtk.Box(spacing=6)
        vbox.pack_start(input_file_box, False, False, 0)
        input_file_label = Gtk.Label(label="Input File:")
        input_file_box.pack_start(input_file_label, False, False, 0)
        self.input_file_chooser = Gtk.FileChooserButton()
        self.input_file_chooser.set_action(Gtk.FileChooserAction.OPEN)
        input_file_box.pack_start(self.input_file_chooser, True, True, 0)

        # Language
        language_box = Gtk.Box(spacing=6)
        vbox.pack_start(language_box, False, False, 0)
        language_label = Gtk.Label(label="Lector Language:")
        language_box.pack_start(language_label, False, False, 0)
        self.language_entry = Gtk.Entry()
        self.language_entry.set_text("pl_PL")
        language_box.pack_start(self.language_entry, True, True, 0)

        # Voice
        voice_box = Gtk.Box(spacing=6)
        vbox.pack_start(voice_box, False, False, 0)
        voice_label = Gtk.Label(label="Lector Voice:")
        voice_box.pack_start(voice_label, False, False, 0)
        self.voice_entry = Gtk.Entry()
        self.voice_entry.set_text("darkman-medium")
        voice_box.pack_start(self.voice_entry, True, True, 0)

        # Model path
        model_path_box = Gtk.Box(spacing=6)
        vbox.pack_start(model_path_box, False, False, 0)
        model_path_label = Gtk.Label(label="Recognization Model Path:")
        model_path_box.pack_start(model_path_label, False, False, 0)
        self.model_path_entry = Gtk.Entry()
        self.model_path_entry.set_text("vosk-model-en-us-0.42-gigaspeech")
        model_path_box.pack_start(self.model_path_entry, True, True, 0)

        # Output file
        output_file_box = Gtk.Box(spacing=6)
        vbox.pack_start(output_file_box, False, False, 0)
        output_file_label = Gtk.Label(label="Output File:")
        output_file_box.pack_start(output_file_label, False, False, 0)
        self.output_file_entry = Gtk.Entry()
        self.output_file_entry.set_text("output.wav")
        output_file_box.pack_start(self.output_file_entry, True, True, 0)
        output_folder_button = Gtk.Button(label="Choose Output Folder")
        output_folder_button.connect("clicked", self.choose_output_folder)
        output_file_box.pack_start(output_folder_button, False, False, 0)

        # Output video file
        output_video_box = Gtk.Box(spacing=6)
        vbox.pack_start(output_video_box, False, False, 0)
        output_video_label = Gtk.Label(label="Output Video File:")
        output_video_box.pack_start(output_video_label, False, False, 0)
        self.output_video_entry = Gtk.Entry()
        self.output_video_entry.set_text("output_video.mp4")
        output_video_box.pack_start(self.output_video_entry, True, True, 0)

        # Generate button
        generate_button = Gtk.Button(label="Generate")
        generate_button.connect("clicked", self.generate_audio)
        vbox.pack_start(generate_button, False, False, 0)

    def generate_audio_from_text(self, text, output_file, language, voice, length_scale=1.0):
        cmd = f"echo '{text}' | piper -c {language}-{voice}.onnx.json -m {language}-{voice}.onnx --length-scale {length_scale} --output_file {output_file}"
        subprocess.run(cmd, shell=True)

    def transcribe_audio_to_srt(self, input_file, output_file, model_path, language):
        cmd = f"vosk-transcriber -m {model_path} -l {language} -i {input_file} -t srt -o {output_file}"
        subprocess.run(cmd, shell=True)

    def translate_srt_file(self, srt_file, translated_srt_file, target_language):
        # Open original SRT file
        with open(srt_file, 'r', encoding='utf-8') as f:
            original_srt_content = f.read()

        # Translate SRT content
        translated_srt_content = GoogleTranslator(source='auto', target=target_language).translate(original_srt_content)

        # Save translated SRT content to a new file
        with open(translated_srt_file, 'w', encoding='utf-8') as f:
            f.write(translated_srt_content)

        # Save translated SRT content to a text file
        text_file_path = translated_srt_file.replace('.srt', '_translated.txt')
        with open(text_file_path, 'w', encoding='utf-8') as text_file:
            text_file.write(translated_srt_content)

        return text_file_path

    def generate_audio_from_srt(self, srt_file, output_file, language, voice, target_language):
        subs = pysrt.open(srt_file)

        audio_clips = []

        for i, sub in enumerate(subs, start=1):
            text = sub.text.replace('\n', ' ')
            start_time_ms = (sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds) * 1000
            end_time_ms = (sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds) * 1000
            duration_ms = end_time_ms - start_time_ms

            translated_text = GoogleTranslator(source='auto', target=target_language).translate(text)

            # Generate preliminary audio clip
            temp_output_file = f"/tmp/temp_{i}.wav"
            self.generate_audio_from_text(translated_text, temp_output_file, language, voice)

            audio_clip = AudioSegment.from_wav(temp_output_file)
            audio_clip_duration_ms = len(audio_clip)

            # Calculate length scale
            length_scale = duration_ms / audio_clip_duration_ms

            # Generate the final audio clip with the correct length scale
            self.generate_audio_from_text(translated_text, temp_output_file, language, voice, length_scale)

            adjusted_audio_clip = AudioSegment.from_wav(temp_output_file)
            audio_clips.append((start_time_ms, adjusted_audio_clip))

            # Remove temporary file
            os.remove(temp_output_file)

        # Combine audio clips with silence between them
        final_audio = AudioSegment.empty()
        prev_end_time_ms = 0

        for start_time_ms, audio_clip in audio_clips:
            if start_time_ms > prev_end_time_ms:
                silence_duration_ms = start_time_ms - prev_end_time_ms
                final_audio += AudioSegment.silent(duration=silence_duration_ms)
            final_audio += audio_clip
            prev_end_time_ms = start_time_ms + len(audio_clip)

        final_audio.export(output_file, format="wav")

    def choose_output_folder(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Output Folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            output_folder = dialog.get_filename()
            output_file_name = os.path.join(output_folder, self.output_file_entry.get_text())
            self.output_file_entry.set_text(output_file_name)
            output_video_name = os.path.join(output_folder, self.output_video_entry.get_text())
            self.output_video_entry.set_text(output_video_name)
        dialog.destroy()

    def generate_audio(self, widget):
        input_file = self.input_file_chooser.get_filename()
        language = self.language_entry.get_text()
        voice = self.voice_entry.get_text()
        model_path = self.model_path_entry.get_text()
        output_file = self.output_file_entry.get_text()
        output_video_file = self.output_video_entry.get_text()
        target_language = self.target_language_entry.get_text()

        if input_file and language and voice and model_path and output_file and output_video_file and target_language:
            base_name, _ = os.path.splitext(input_file)
            srt_file = f"{base_name}.srt"

            # Transcribe audio to SRT using vosk
            self.transcribe_audio_to_srt(input_file, srt_file, model_path, language)

            # Generate audio from SRT
            self.generate_audio_from_srt(srt_file, output_file, language, voice, target_language)

            # Replace audio in video
            self.replace_audio_in_video(input_file, output_file, output_video_file)

            # Translate SRT file
            translated_srt_file = f"{base_name}_translated.srt"
            text_file_path = self.translate_srt_file(srt_file, translated_srt_file, target_language)
    
            # Do something with the text file path if needed

        else:
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format="Please fill in all fields.",
            )
            dialog.run()
            dialog.destroy()

    def get_silent_audio(self, duration_ms):
        return AudioSegment.silent(duration=duration_ms)

    def replace_audio_in_video(self, input_video, new_audio, output_video):
        video = VideoFileClip(input_video)
        audio = AudioFileClip(new_audio)

        new_video = video.set_audio(audio)
        new_video.write_videofile(output_video)

win = AudioSubGenerator()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
