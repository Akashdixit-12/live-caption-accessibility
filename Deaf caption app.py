"""
Deaf Accessibility - Live Caption App
=======================================
Zoom/Meet ke upar ek floating window chalti hai
jisme real-time captions dikhte hain deaf users ke liye.

Libraries: numpy, pandas, matplotlib, scikit-learn, SpeechRecognition, tkinter
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import speech_recognition as sr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
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
# 2. IMPORTANCE CLASSIFIER (scikit-learn)
# ─────────────────────────────────────────────

class ImportanceClassifier:
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=300, stop_words='english')),
            ('clf', MultinomialNB())
        ])
        self._train()

    def _train(self):
        important = [
            "The deadline is next Friday",
            "Please review the document",
            "Action item send the report",
            "Critical issue found in system",
            "Meeting rescheduled to tomorrow",
            "Important update for everyone",
            "Please share your screen now",
            "The client approved the proposal",
            "Password reset required immediately",
            "Budget finalized by end of day",
            "Emergency meeting called right now",
            "Please join the call urgently",
        ]
        filler = [
            "Um yeah I think so",
            "Okay sure sounds good",
            "Can everyone hear me",
            "Sorry I was on mute",
            "Yeah okay moving on",
            "Hmm let me think",
            "Just one second please",
            "Alright so anyway yeah",
            "Let me share my screen",
            "Okay great thanks everyone",
            "Hold on just a moment",
            "Yep got it okay",
        ]
        texts = important + filler
        labels = ['important'] * len(important) + ['filler'] * len(filler)
        self.pipeline.fit(texts, labels)

    def classify(self, text):
        try:
            return self.pipeline.predict([text])[0]
        except:
            return 'filler'


# ─────────────────────────────────────────────
# 3. AUDIO ANALYZER (numpy)
# ─────────────────────────────────────────────

class AudioAnalyzer:
    def compute_rms(self, signal):
        arr = np.frombuffer(signal, dtype=np.int16).astype(np.float32)
        return np.sqrt(np.mean(arr ** 2))

    def is_loud_enough(self, signal, threshold=300):
        return self.compute_rms(signal) > threshold


# ─────────────────────────────────────────────
# 4. FLOATING CAPTION WINDOW (tkinter)
# ─────────────────────────────────────────────

class CaptionWindow:
    def __init__(self, logger, classifier):
        self.logger = logger
        self.classifier = classifier
        self.is_listening = False
        self.recognizer = sr.Recognizer()
        self.audio_analyzer = AudioAnalyzer()

        # Main window
        self.root = tk.Tk()
        self.root.title("🎤 Live Captions — Deaf Accessibility")
        self.root.geometry("900x280")
        self.root.configure(bg='#0a0a0a')

        # Always on top — Zoom/Meet ke upar dikhe
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.93)

        self._build_ui()

    def _build_ui(self):
        # ── Top bar ──
        top = tk.Frame(self.root, bg='#111111', pady=6)
        top.pack(fill='x')

        tk.Label(top, text="👂 LIVE CAPTIONS",
                 bg='#111111', fg='#00e5ff',
                 font=('Helvetica', 13, 'bold')).pack(side='left', padx=14)

        self.status_label = tk.Label(top, text="● Ruka hua hai",
                                      bg='#111111', fg='#555555',
                                      font=('Helvetica', 11))
        self.status_label.pack(side='left', padx=10)

        tk.Button(top, text="📊 Report",
                  bg='#1a1a2e', fg='white',
                  font=('Helvetica', 10), relief='flat',
                  padx=10, command=self._show_report).pack(side='right', padx=6)

        tk.Button(top, text="💾 Save CSV",
                  bg='#1a1a2e', fg='white',
                  font=('Helvetica', 10), relief='flat',
                  padx=10, command=self._save_csv).pack(side='right', padx=6)

        self.btn = tk.Button(top, text="🎤 START",
                             bg='#00c853', fg='black',
                             font=('Helvetica', 11, 'bold'),
                             relief='flat', padx=16,
                             command=self._toggle)
        self.btn.pack(side='right', padx=10)

        # ── Caption display area ──
        caption_frame = tk.Frame(self.root, bg='#0a0a0a')
        caption_frame.pack(fill='both', expand=True, padx=16, pady=10)

        self.importance_indicator = tk.Label(
            caption_frame, text="",
            bg='#0a0a0a', fg='#ffd740',
            font=('Helvetica', 11, 'bold')
        )
        self.importance_indicator.pack(anchor='w')

        self.caption_var = tk.StringVar(value="Yahan live captions dikhenge...")
        self.caption_label = tk.Label(
            caption_frame,
            textvariable=self.caption_var,
            bg='#0a0a0a', fg='white',
            font=('Helvetica', 26, 'bold'),
            wraplength=860,
            justify='left'
        )
        self.caption_label.pack(anchor='w', pady=(4, 0))

        # ── Bottom history bar ──
        self.history_var = tk.StringVar(value="")
        tk.Label(self.root,
                 textvariable=self.history_var,
                 bg='#111111', fg='#555555',
                 font=('Helvetica', 10),
                 wraplength=880, justify='left',
                 pady=5).pack(fill='x', padx=14)

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

            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.status_label.config(
                    text="● Samajh nahi aaya, dobara bolo", fg='#ff9800'))
            except Exception as e:
                if self.is_listening:
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"● Error: {str(e)[:30]}", fg='#ff4444'))

    def _update_caption(self, text, importance):
        # Caption update karo
        self.caption_var.set(text)

        if importance == 'important':
            self.caption_label.config(fg='#ffd740')
            self.importance_indicator.config(text="⭐ IMPORTANT")
        else:
            self.caption_label.config(fg='white')
            self.importance_indicator.config(text="")

        self.status_label.config(text="● Sun raha hun...", fg='#00e5ff')

        # History mein add karo
        total = len(self.logger.df)
        self.history_var.set(
            f"Total captions: {total}  |  "
            f"Important: {int((self.logger.df['importance'] == 'important').sum())}  |  "
            f"Words: {int(self.logger.df['word_count'].sum())}"
        )

    def _save_csv(self):
        if self.logger.df.empty:
            self.caption_var.set("Pehle kuch bolo! Koi caption nahi hai abhi.")
            return
        filename = self.logger.save_csv()
        self.caption_var.set(f"✅ Saved: {filename}")

    def _show_report(self):
        if self.logger.df.empty:
            self.caption_var.set("Pehle kuch bolo! Report ke liye data chahiye.")
            return

        summary = self.logger.get_summary()
        keywords = self.logger.get_top_keywords()

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('#0d1117')
        fig.suptitle('Meeting Caption Report', color='white',
                     fontsize=14, fontweight='bold')

        # Chart 1: Summary
        ax1 = axes[0]
        ax1.set_facecolor('#161b22')
        keys = list(summary.keys())
        vals = [str(v) for v in summary.values()]
        y_pos = range(len(keys))
        bars = ax1.barh(y_pos, [summary[k] if isinstance(summary[k], (int, float))
                                else 1 for k in keys],
                        color='#00e5ff', alpha=0.8)
        ax1.set_yticks(list(y_pos))
        ax1.set_yticklabels(keys, color='white')
        ax1.set_title('Session Summary', color='white')
        ax1.tick_params(colors='gray')
        for spine in ax1.spines.values():
            spine.set_edgecolor('#30363d')
        for i, (bar, val) in enumerate(zip(bars, vals)):
            ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                     val, va='center', color='white', fontsize=9)

        # Chart 2: Keywords
        ax2 = axes[1]
        ax2.set_facecolor('#161b22')
        if not keywords.empty:
            ax2.barh(keywords.index, keywords.values,
                     color='#ff4081', alpha=0.85)
            ax2.set_title('Top Keywords', color='white')
            ax2.tick_params(colors='white')
            for spine in ax2.spines.values():
                spine.set_edgecolor('#30363d')
        else:
            ax2.text(0.5, 0.5, 'Not enough data', ha='center',
                     va='center', color='gray', transform=ax2.transAxes)

        plt.tight_layout()
        plt.savefig('caption_report.png', dpi=150,
                    bbox_inches='tight', facecolor='#0d1117')
        plt.show()
        print("[✓] Report saved: caption_report.png")

    def run(self):
        self.root.mainloop()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Deaf Accessibility — Live Caption App")
    print("=" * 50)
    print("\n[SETUP] Models load ho rahe hain...")

    logger = CaptionLogger()
    classifier = ImportanceClassifier()

    print("[✓] Ready! Window khul rahi hai...\n")
    print("HOW TO USE:")
    print("  1. START button dabao")
    print("  2. Zoom/Meet pe video call karo")
    print("  3. Yeh window upar rehegi — captions dikhte rahenge")
    print("  4. ⭐ yellow = important caption")
    print("  5. Report/Save se data dekho\n")

    app = CaptionWindow(logger, classifier)
    app.run()