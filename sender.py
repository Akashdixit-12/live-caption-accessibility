"""
SENDER — Tera laptop pe chalao
================================
Tu bolega → captions dusre ke screen pe jaayenge
Same WiFi pe hona zaroori hai dono ka
"""

import socket
import threading
import speech_recognition as sr
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from datetime import datetime
import tkinter as tk
import warnings
warnings.filterwarnings('ignore')


# ─── Importance Classifier (sklearn) ───
class ImportanceClassifier:
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=300, stop_words='english')),
            ('clf', MultinomialNB())
        ])
        important = [
            "deadline is next friday", "please review the document",
            "action item send report", "critical issue found",
            "meeting rescheduled", "important update for everyone",
            "client approved proposal", "emergency meeting now",
            "please join urgently", "budget finalized today",
        ]
        filler = [
            "um yeah okay", "sure sounds good", "can you hear me",
            "sorry i was mute", "just one second", "alright anyway",
            "hmm let me think", "okay great thanks", "hold on moment", "yep got it",
        ]
        self.pipeline.fit(important + filler,
                          ['important']*len(important) + ['filler']*len(filler))

    def classify(self, text):
        try:
            return self.pipeline.predict([text])[0]
        except:
            return 'filler'


# ─── Caption Logger (pandas) ───
class CaptionLogger:
    def __init__(self):
        self.df = pd.DataFrame(columns=['time', 'text', 'importance'])

    def add(self, text, importance):
        row = {'time': datetime.now().strftime('%H:%M:%S'),
               'text': text, 'importance': importance}
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)

    def save(self):
        f = f"sent_captions_{datetime.now().strftime('%H%M%S')}.csv"
        self.df.to_csv(f, index=False)
        return f


# ─── Main Sender App ───
class SenderApp:
    def __init__(self):
        self.classifier = ImportanceClassifier()
        self.logger = CaptionLogger()
        self.recognizer = sr.Recognizer()
        self.client_socket = None
        self.is_listening = False

        self._build_ui()

    def _build_ui(self):
        self.root = tk.Tk()
        self.receiver_ip = tk.StringVar(value="")
        self.root.title("🎤 SENDER — Tera App")
        self.root.geometry("600x420")
        self.root.configure(bg='#0a0a0a')
        self.root.attributes('-topmost', True)

        # Title
        tk.Label(self.root, text="🎤 SENDER APP — Tera Laptop",
                 bg='#0a0a0a', fg='#00e5ff',
                 font=('Helvetica', 15, 'bold')).pack(pady=(16, 4))

        tk.Label(self.root,
                 text="Tu bolega → Deaf person ke screen pe captions jaayenge",
                 bg='#0a0a0a', fg='#888888',
                 font=('Helvetica', 10)).pack()

        # IP input
        ip_frame = tk.Frame(self.root, bg='#0a0a0a')
        ip_frame.pack(pady=16)

        tk.Label(ip_frame, text="Deaf person ka IP address:",
                 bg='#0a0a0a', fg='white',
                 font=('Helvetica', 11)).pack(side='left', padx=(0, 8))

        self.ip_entry = tk.Entry(ip_frame, textvariable=self.receiver_ip,
                                  font=('Helvetica', 13), width=16,
                                  bg='#1a1a1a', fg='white',
                                  insertbackground='white',
                                  relief='flat', bd=6)
        self.ip_entry.pack(side='left')
        self.ip_entry.insert(0, "192.168.x.x")

        # Connect button
        self.connect_btn = tk.Button(
            self.root, text="🔗 Connect karo",
            bg='#1565c0', fg='white',
            font=('Helvetica', 11, 'bold'),
            relief='flat', padx=14, pady=6,
            command=self._connect
        )
        self.connect_btn.pack(pady=6)

        # Status
        self.status = tk.Label(self.root,
                                text="● Pehle connect karo",
                                bg='#0a0a0a', fg='#888888',
                                font=('Helvetica', 11))
        self.status.pack(pady=4)

        # Current caption
        tk.Label(self.root, text="Jo tu bol raha hai:",
                 bg='#0a0a0a', fg='#555555',
                 font=('Helvetica', 10)).pack(pady=(12, 2))

        self.caption_var = tk.StringVar(value="...")
        tk.Label(self.root,
                 textvariable=self.caption_var,
                 bg='#111111', fg='white',
                 font=('Helvetica', 18, 'bold'),
                 wraplength=560, justify='center',
                 pady=14, padx=20).pack(fill='x', padx=20)

        # Start/Stop button
        self.mic_btn = tk.Button(
            self.root, text="🎤 Bolna Shuru Karo",
            bg='#555555', fg='white',
            font=('Helvetica', 12, 'bold'),
            relief='flat', padx=20, pady=8,
            state='disabled',
            command=self._toggle_mic
        )
        self.mic_btn.pack(pady=14)

        # Stats
        self.stats_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.stats_var,
                 bg='#0a0a0a', fg='#555555',
                 font=('Helvetica', 9)).pack()

    def _connect(self):
        ip = self.receiver_ip.get().strip()
        if not ip or ip == "192.168.x.x":
            self.status.config(text="❌ Sahi IP daalo!", fg='#ff4444')
            return

        try:
            self.status.config(text="● Connect ho raha hai...", fg='#ffd740')
            self.root.update()

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((ip, 9999))
            self.client_socket.settimeout(None)

            self.status.config(text="✅ Connected! Ab bol sakta hai", fg='#00e5ff')
            self.connect_btn.config(state='disabled')
            self.mic_btn.config(state='normal', bg='#00c853', fg='black')

        except Exception as e:
            self.status.config(text=f"❌ Connect nahi hua — Receiver pehle chalao!",
                               fg='#ff4444')
            self.client_socket = None

    def _toggle_mic(self):
        if not self.is_listening:
            self.is_listening = True
            self.mic_btn.config(text="⏹ Band Karo", bg='#d50000', fg='white')
            self.status.config(text="● Sun raha hun...", fg='#00e5ff')
            threading.Thread(target=self._listen_loop, daemon=True).start()
        else:
            self.is_listening = False
            self.mic_btn.config(text="🎤 Bolna Shuru Karo", bg='#00c853', fg='black')
            self.status.config(text="● Ruka hua hai", fg='#888888')
            # Save CSV
            if not self.logger.df.empty:
                f = self.logger.save()
                self.stats_var.set(f"Saved: {f}")

    def _listen_loop(self):
        while self.is_listening:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)

                    # numpy se volume check
                    raw = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                    if np.sqrt(np.mean(raw.astype(np.float32)**2)) < 200:
                        continue

                    text = self.recognizer.recognize_google(audio, language='en-IN')
                    if text and self.client_socket:
                        importance = self.classifier.classify(text)
                        self.logger.add(text, importance)

                        # Dusre ko bhejo
                        message = f"{importance}||{text}"
                        self.client_socket.send(message.encode('utf-8'))

                        # Apni screen pe bhi dikhao
                        self.root.after(0, self._show_caption, text, importance)

            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.status.config(
                    text="● Samajh nahi aaya...", fg='#ff9800'))
            except Exception as e:
                if self.is_listening:
                    self.root.after(0, lambda: self.status.config(
                        text=f"● Error: {str(e)[:40]}", fg='#ff4444'))

    def _show_caption(self, text, importance):
        self.caption_var.set(text)
        self.status.config(text="● Sun raha hun...", fg='#00e5ff')
        total = len(self.logger.df)
        imp = int((self.logger.df['importance'] == 'important').sum())
        self.stats_var.set(f"Bheje: {total} captions | Important: {imp}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("=" * 50)
    print("  SENDER APP — Tera Laptop")
    print("=" * 50)
    print("\nSteps:")
    print("1. Pehle RECEIVER app deaf person ke laptop pe chalao")
    print("2. Unka IP address lo (receiver app mein dikhega)")
    print("3. Woh IP yahan daalo aur Connect karo")
    print("4. Phir bolna shuru karo!\n")
    app = SenderApp()
    app.run()