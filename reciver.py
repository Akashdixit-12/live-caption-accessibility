"""
RECEIVER — Deaf Person ke Laptop pe chalao
===========================================
Dusre ka bola hua → Yahan bade captions mein dikhega
Same WiFi pe hona zaroori hai
"""




from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


# ─── Caption Logger (pandas) ───
class CaptionLogger:
    def __init__(self):
        self.df = pd.DataFrame(columns=['time', 'text', 'importance'])

    def add(self, text, importance):
        row = {'time': datetime.now().strftime('%H:%M:%S'),
               'text': text, 'importance': importance}
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)

    def save(self):
        f = f"received_captions_{datetime.now().strftime('%H%M%S')}.csv"
        self.df.to_csv(f, index=False)
        return f

    def get_keywords(self):
        if self.df.empty:
            return pd.Series(dtype=int)
        all_words = ' '.join(self.df['text'].tolist())
        words = [w.lower() for w in all_words.split() if len(w) > 3]
        return pd.Series(words).value_counts().head(8)


# ─── Main Receiver App ───
class ReceiverApp:
    def __init__(self):
        self.logger = CaptionLogger()
        self.server_socket = None
        self.conn = None
        self.my_ip = self._get_ip()

        self._build_ui()
        self._start_server()

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "IP nahi mila"
    def _server_loop(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', 9999))
            self.server_socket.listen(1)

            self.root.after(0, lambda: self.status.config(
                text=f"● Sender ka wait kar raha hun... ({self.my_ip})",
                fg='#ffd740'))

            self.conn, addr = self.server_socket.accept()

            self.root.after(0, lambda: self.status.config(
                text=f"✅ Connected! Captions aa rahe hain...",
                fg='#00e5ff'))
            self.root.after(0, lambda: self.caption_var.set(
                "Connected! Dusra ab bolna shuru kare..."))

            # Captions receive karo
            while True:
                data = self.conn.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                if '||' in message:
                    importance, text = message.split('||', 1)
                    self.root.after(0, self._show_caption, text, importance)

        except Exception as e:
            if "closed" not in str(e).lower():
                self.root.after(0, lambda: self.status.config(
                    text=f"❌ Error: {str(e)[:40]}", fg='#ff4444'))

    def _show_caption(self, text, importance):
        # Purana caption neeche karo
        current = self.caption_var.get()
        if current not in ["Yahan captions dikhenge...",
                            "Connected! Dusra ab bolna shuru kare..."]:
            self.prev_var.set(current)

        # Naya caption dikhao
        self.caption_var.set(text)
        self.logger.add(text, importance)

        if importance == 'important':
            self.caption_label.config(fg='#ffd740')
            self.importance_label.config(text="⭐ IMPORTANT — DHYAN DO!")
            self.root.configure(bg='#1a0a00')
            self.caption_label.configure(bg='#1a0a00')
            self.importance_label.configure(bg='#1a0a00')
            self.prev_var.master.configure(bg='#1a0a00') if hasattr(
                self.prev_var, 'master') else None
            # 3 second baad normal kar do
            self.root.after(3000, self._reset_bg)
        else:
            self.caption_label.config(fg='white')
            self.importance_label.config(text="")

        # Stats update
        total = len(self.logger.df)
        imp = int((self.logger.df['importance'] == 'important').sum())
        self.stats_var.set(
            f"Mile: {total} captions  |  Important: {imp}  |  "
            f"Words: {int(self.logger.df['text'].apply(lambda x: len(x.split())).sum())}"
        )

    def _reset_bg(self):
        self.root.configure(bg='#000000')
        self.caption_label.configure(bg='#000000')
        self.importance_label.configure(bg='#000000', text="")

    def _clear(self):
        self.caption_var.set("Screen clear hua!")
        self.prev_var.set("")
        self.importance_label.config(text="")

    def _save(self):
        if self.logger.df.empty:
            self.caption_var.set("Koi caption nahi abhi!")
            return
        f = self.logger.save()
        self.caption_var.set(f"✅ Saved: {f}")

    def _show_report(self):
        if self.logger.df.empty:
            self.caption_var.set("Pehle kuch captions aane do!")
            return

        keywords = self.logger.get_keywords()
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('#0d1117')
        fig.suptitle('Conversation Report', color='white',
                     fontsize=14, fontweight='bold')

        # Important vs Filler
        ax1 = axes[0]
        ax1.set_facecolor('#161b22')
        counts = self.logger.df['importance'].value_counts()
        colors = ['#ffd740' if i == 'important' else '#00e5ff'
                  for i in counts.index]
        ax1.pie(counts.values, labels=counts.index,
                colors=colors, autopct='%1.0f%%', startangle=140)
        for text in ax1.texts:
            text.set_color('white')
        ax1.set_title('Important vs Normal', color='white')

        # Keywords
        ax2 = axes[1]
        ax2.set_facecolor('#161b22')
        if not keywords.empty:
            ax2.barh(keywords.index, keywords.values,
                     color='#ff4081', alpha=0.85)
            ax2.set_title('Top Keywords', color='white')
            ax2.tick_params(colors='white')
            for spine in ax2.spines.values():
                spine.set_edgecolor('#30363d')

        plt.tight_layout()
        plt.savefig('conversation_report.png', dpi=150,
                    bbox_inches='tight', facecolor='#0d1117')
        plt.show()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("=" * 50)
    print("  RECEIVER APP — Deaf Person ka Laptop")
    print("=" * 50)
    print("\nYeh app chalao pehle!")
    print("Apna IP address sender ko batao")
    print("Phir sender connect karega aur captions aane shuru honge!\n")
    app = ReceiverApp()
    app.run()
