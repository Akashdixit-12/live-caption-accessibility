"""
Deaf Accessibility - Live Caption App
=======================================
Zoom/Meet ke upar ek floating window chalti hai
jisme real-time captions dikhte hain deaf users ke liye.

Libraries: numpy, pandas, matplotlib, SpeechRecognition
"""

import speech_recognition as sr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ─────────────────────────────────────────────
# 1. CAPTION LOGGER (pandas)
# ─────────────────────────────────────────────

class CaptionLogger:
    def __init__(self):
        self.df = pd.DataFrame(columns=[
            'timestamp', 'caption_text', 'confidence',
            'word_count', 'importance'
        ])

    def add(self, text, confidence, importance):
        row = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'caption_text': text,
            'confidence': confidence,
            'word_count': len(text.split()),
            'importance': importance
        }
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)

    def get_summary(self):
        if self.df.empty:
            return {}
        return {
            'Total Captions': len(self.df),
            'Total Words': int(self.df['word_count'].sum()),
            'Avg Confidence': round(float(self.df['confidence'].mean()), 2),
            'Important Lines': int((self.df['importance'] == 'important').sum()),
        }

    def save_csv(self):
        filename = f"captions_{datetime.now().strftime('%H%M%S')}.csv"
        self.df.to_csv(filename, index=False)
        return filename

    def get_top_keywords(self):
        if self.df.empty:
            return pd.Series(dtype=int)
        all_words = ' '.join(self.df['caption_text'].tolist())
        words = [w.lower() for w in all_words.split() if len(w) > 3]
        return pd.Series(words).value_counts().head(8)





# ─────────────────────────────────────────────
# 3. AUDIO ANALYZER (numpy)
# ─────────────────────────────────────────────

class AudioAnalyzer:
    def compute_rms(self, signal):
        arr = np.frombuffer(signal, dtype=np.int16).astype(np.float32)
        return np.sqrt(np.mean(arr ** 2))

    def is_loud_enough(self, signal, threshold=300):
        return self.compute_rms(signal) > threshold


    def _toggle(self):
        if not self.is_listening:
            self.is_listening = True
            self.btn.config(text="⏹ STOP", bg='#d50000')
            self.status_label.config(text="● Sun raha hun...", fg='#00e5ff')
            threading.Thread(target=self._listen_loop, daemon=True).start()
        else:
            self.is_listening = False
            self.btn.config(text="🎤 START", bg='#00c853')
            self.status_label.config(text="● Ruka hua hai", fg='#555555')
            self.caption_var.set("Yahan live captions dikhenge...")
            self.importance_indicator.config(text="")

    def _listen_loop(self):
        while self.is_listening:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    self.root.after(0, lambda: self.status_label.config(
                        text="● Sun raha hun...", fg='#00e5ff'))
                    audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)

                    # numpy se audio analyze karo
                    raw = audio.get_raw_data()
                    if not self.audio_analyzer.is_loud_enough(raw):
                        continue

                    text = self.recognizer.recognize_google(audio, language='en-IN')
                    if text:
                        importance = self.classifier.classify(text)
                        self.logger.add(text, 0.92, importance)
                        self.root.after(0, self._update_caption, text, importance)
