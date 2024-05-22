import subprocess
import os
from pydub import AudioSegment
import pysrt
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from moviepy.editor import VideoFileClip, AudioFileClip

class AudioSubGenerator(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Lector_Replacer")
        self.set_border_width(10)
        self.set_default_size(400, 300)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

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
        language_label = Gtk.Label(label="Language:")
        language_box.pack_start(language_label, False, False, 0)
        self.language_entry = Gtk.Entry()
        self.language_entry.set_text("pl_PL")
        language_box.pack_start(self.language_entry, True, True, 0)

        # Voice
        voice_box = Gtk.Box(spacing=6)
        vbox.pack_start(voice_box, False, False, 0)
        voice_label = Gtk.Label(label="Voice:")
        voice_box.pack_start(voice_label, False, False, 0)
        self.voice_entry = Gtk.Entry()
        self.voice_entry.set_text("darkman-medium")
        voice_box.pack_start(self.voice_entry, True, True, 0)

        # Model path
        model_path_box = Gtk.Box(spacing=6)
        vbox.pack_start(model_path_box, False, False, 0)
        model_path_label = Gtk.Label(label="Model Path:")
        model_path_box.pack_start(model_path_label, False, False, 0)
        self.model_path_entry = Gtk.Entry()
        self.model_path_entry.set_text("vosk-model-small-pl-0.22")
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

    def generate_audio_from_text(self, text, output_file, language, voice):
        cmd = f"echo '{text}' | piper -c {language}-{voice}.onnx.json -m {language}-{voice}.onnx --output_file {output_file}"
        subprocess.run(cmd, shell=True)

    def transcribe_audio_to_srt(self, input_file, output_file, model_path, language):
        cmd = f"vosk-transcriber -m {model_path} -l {language} -i {input_file} -t srt -o {output_file}"
        subprocess.run(cmd, shell=True)

    def generate_audio_from_srt(self, srt_file, output_file, language, voice):
        subs = pysrt.open(srt_file)

        audio_clips = []
        for sub in subs:
            text = sub.text.replace('\n', ' ')
            start_time = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds
            end_time = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds
            duration = end_time - start_time

            cmd = f"echo '{text}' | piper -c {language}-{voice}.onnx.json -m {language}-{voice}.onnx --output_file /tmp/temp.wav"
            subprocess.run(cmd, shell=True)

            audio_clip = AudioSegment.from_wav("/tmp/temp.wav")
            audio_clip = audio_clip._spawn(audio_clip.raw_data, overrides={
                "frame_rate": audio_clip.frame_rate,
                "channels": audio_clip.channels,
                "sample_width": audio_clip.sample_width,
                "duration": duration * 1000,  # Convert to milliseconds
            })
            audio_clips.append(audio_clip)

        final_audio = sum(audio_clips)
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

        if input_file and language and voice and model_path and output_file and output_video_file:
            base_name, _ = os.path.splitext(input_file)
            srt_file = f"{base_name}.srt"

            # Transcribe audio to SRT using vosk
            self.transcribe_audio_to_srt(input_file, srt_file, model_path, language)

            # Generate audio from SRT
            self.generate_audio_from_srt(srt_file, output_file, language, voice)

            # Replace audio in video
            self.replace_audio_in_video(input_file, output_file, output_video_file)
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

    def replace_audio_in_video(self, input_video, new_audio, output_video):
        video = VideoFileClip(input_video)
        audio = AudioFileClip(new_audio)

        new_video = video.set_audio(audio)
        new_video.write_videofile(output_video)

win = AudioSubGenerator()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
