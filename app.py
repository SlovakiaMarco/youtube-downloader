import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import yt_dlp

# Nastavenie vzhľadu CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class MediaDownloaderApp(ctk.CTk):

  def __init__(self):
    super().__init__()

    # Nastavenie okna
    self.title("Media Downloader Pro (Premiere Ready)")
    self.geometry("620x520")
    self.resizable(False, False)

    # Premenné
    self.download_folder = tk.StringVar(value=os.path.expanduser("~/Downloads"))
    self.mode_var = tk.StringVar(value="video")

    self._build_ui()

  def _build_ui(self):
    # Nadpis
    self.title_label = ctk.CTkLabel(
        self,
        text="Video & Audio Downloader",
        font=ctk.CTkFont(size=22, weight="bold"),
    )
    self.title_label.pack(pady=(20, 10))

    # Frame pre URL
    self.url_frame = ctk.CTkFrame(self)
    self.url_frame.pack(padx=20, pady=10, fill="x")

    self.url_label = ctk.CTkLabel(
        self.url_frame, text="URL adresa videa:", font=ctk.CTkFont(size=13)
    )
    self.url_label.pack(anchor="w", padx=15, pady=(10, 2))

    self.url_entry = ctk.CTkEntry(
        self.url_frame,
        placeholder_text="https://www.youtube.com/watch?v=...",
        height=38,
    )
    self.url_entry.pack(fill="x", padx=15, pady=(0, 15))

    # Frame pre Voľby (Typ súboru + Priečinok)
    self.opts_frame = ctk.CTkFrame(self)
    self.opts_frame.pack(padx=20, pady=10, fill="x")

    # Typ stiahnutia (Video / Audio)
    self.type_label = ctk.CTkLabel(
        self.opts_frame, text="Režim sťahovania:", font=ctk.CTkFont(size=13)
    )
    self.type_label.pack(anchor="w", padx=15, pady=(10, 5))

    self.radio_frame = ctk.CTkFrame(self.opts_frame, fg_color="transparent")
    self.radio_frame.pack(anchor="w", padx=15, pady=(0, 10))

    self.radio_video = ctk.CTkRadioButton(
        self.radio_frame,
        text="Video (MP4 / AVC + AAC - Premiere Compatible)",
        variable=self.mode_var,
        value="video",
    )
    self.radio_video.pack(side="left", padx=(0, 15))

    self.radio_audio = ctk.CTkRadioButton(
        self.radio_frame,
        text="Iba Zvuk (MP3)",
        variable=self.mode_var,
        value="audio",
    )
    self.radio_audio.pack(side="left")

    # Výber priečinka
    self.dir_label = ctk.CTkLabel(
        self.opts_frame, text="Uložiť do:", font=ctk.CTkFont(size=13)
    )
    self.dir_label.pack(anchor="w", padx=15, pady=(5, 2))

    self.dir_inner_frame = ctk.CTkFrame(
        self.opts_frame, fg_color="transparent"
    )
    self.dir_inner_frame.pack(fill="x", padx=15, pady=(0, 15))

    self.dir_entry = ctk.CTkEntry(
        self.dir_inner_frame, textvariable=self.download_folder, height=35
    )
    self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

    self.browse_btn = ctk.CTkButton(
        self.dir_inner_frame,
        text="Prehliadať",
        width=100,
        height=35,
        command=self.browse_folder,
    )
    self.browse_btn.pack(side="right")

    # Štátus a Progress bar
    self.status_label = ctk.CTkLabel(
        self, text="Pripravený", font=ctk.CTkFont(size=12), text_color="gray"
    )
    self.status_label.pack(pady=(15, 2))

    self.progress_bar = ctk.CTkProgressBar(self, width=540)
    self.progress_bar.set(0)
    self.progress_bar.pack(pady=(0, 15))

    # Tlačidlo Štart
    self.download_btn = ctk.CTkButton(
        self,
        text="Stiahnuť",
        font=ctk.CTkFont(size=15, weight="bold"),
        height=42,
        command=self.start_download_thread,
    )
    self.download_btn.pack(padx=20, pady=(0, 20), fill="x")

  def browse_folder(self):
    selected = filedialog.askdirectory(initialdir=self.download_folder.get())
    if selected:
      self.download_folder.set(selected)

  def progress_hook(self, d):
    if d["status"] == "downloading":
      total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
      downloaded = d.get("downloaded_bytes", 0)
      if total > 0:
        percent = downloaded / total
        self.progress_bar.set(percent)
        speed = d.get("_speed_str", "N/A")
        self.status_label.configure(
            text=f"Sťahuje sa... {int(percent * 100)}% ({speed})"
        )
    elif d["status"] == "finished":
      self.status_label.configure(text="Spracovávam súbor pre Premiere Pro...")

  def start_download_thread(self):
    url = self.url_entry.get().strip()
    if not url:
      messagebox.showwarning("Upozornenie", "Zadaj platnú URL adresu!")
      return

    self.download_btn.configure(state="disabled")
    self.progress_bar.set(0)
    self.status_label.configure(text="Pripravujem...", text_color="white")

    # Spustenie v samostatnom vlákne, aby UI nezamrzlo
    threading.Thread(target=self.run_download, args=(url,), daemon=True).start()

  def run_download(self, url):
    output_dir = self.download_folder.get()
    mode = self.mode_var.get()

    outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")

    if mode == "video":
      # Špeciálny formát: vynucujeme H.264 video + AAC audio a MP4 kontajner pre Premiere Pro
      ydl_opts = {
          "format": (
              "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[ext=mp4]/best"
          ),
          "outtmpl": outtmpl,
          "progress_hooks": [self.progress_hook],
          "merge_output_format": "mp4",
          "postprocessors": [{
              "key": "FFmpegVideoConvertor",
              "preferedformat": "mp4",
          }],
      }
    else:
      # Výber iba audia -> konverzia do MP3
      ydl_opts = {
          "format": "bestaudio/best",
          "outtmpl": outtmpl,
          "progress_hooks": [self.progress_hook],
          "postprocessors": [{
              "key": "FFmpegExtractAudio",
              "preferredcodec": "mp3",
              "preferredquality": "320",
          }],
      }

    try:
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

      self.progress_bar.set(1.0)
      self.status_label.configure(
          text="Sťahovanie dokončené!", text_color="#2FA572"
      )
      messagebox.showinfo("Hotovo", "Súbor bol úspešne stiahnutý a uložený.")
    except Exception as e:
      self.status_label.configure(text="Chyba pri sťahovaní", text_color="red")
      messagebox.showerror("Chyba", f"Nastala chyba:\n{str(e)}")
    finally:
      self.download_btn.configure(state="normal")


if __name__ == "__main__":
  app = MediaDownloaderApp()
  app.mainloop()