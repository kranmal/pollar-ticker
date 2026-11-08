"""Scrolling desktop news ticker for Pollar (https://pollar.news) using its public RSS feed."""
import argparse
import json
import os
import sys
import threading
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QWidget

DEFAULT_FEED = "https://pollar.news/en/feed.xml"
UA = "pollar-ticker/0.1 (+https://github.com/kranmal/pollar-ticker)"
CFG = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
                   "pollar-ticker", "config.json")
SEP = "   ◆   "


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        root = ET.fromstring(r.read())
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        cats = [c.text for c in it.findall("category") if c.text]
        if title:
            items.append({"title": title, "link": link, "cat": cats[0] if cats else ""})
    return items


def load_cfg():
    try:
        with open(CFG) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cfg(c):
    try:
        os.makedirs(os.path.dirname(CFG), exist_ok=True)
        with open(CFG, "w") as f:
            json.dump(c, f)
    except OSError:
        pass


class Ticker(QWidget):
    loaded = Signal()

    def __init__(self, feed, refresh_min, cfg):
        super().__init__()
        self.feed, self.cfg = feed, cfg
        self.items, self.status = [], "Loading Pollar…"
        self.speed = cfg.get("speed", 60)        # px/s
        self.alpha = cfg.get("alpha", 200)
        self.at_top = cfg.get("top", False)
        self.paused = False
        self.x = 0.0
        self.segs = []                            # (x0, x1, item)
        self.total = 1
        self.setWindowTitle("pollar-ticker")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.loaded.connect(self.layout_segments)
        self.font_ = QFont("Sans", 12)
        self.font_b = QFont("Sans", 12, QFont.Bold)
        self.place()
        t = QTimer(self); t.timeout.connect(self.tick); t.start(16)
        r = QTimer(self); r.timeout.connect(self.refresh); r.start(refresh_min * 60_000)
        self.refresh()

    def place(self):
        g = QApplication.primaryScreen().geometry()
        h = 34
        self.setGeometry(g.x(), g.y() if self.at_top else g.y() + g.height() - h, g.width(), h)

    def refresh(self):
        def work():
            try:
                items = fetch(self.feed)
                self.items, self.status = items, ""
                self.loaded.emit()
            except Exception as e:
                if not self.items:
                    self.status = f"Pollar feed error: {e}"
        threading.Thread(target=work, daemon=True).start()

    def layout_segments(self):
        fm, fb = QFontMetrics(self.font_), QFontMetrics(self.font_b)
        x, segs = 0, []
        for it in self.items:
            tag = f"[{it['cat']}] " if it["cat"] else ""
            w = fb.horizontalAdvance(tag) + fm.horizontalAdvance(it["title"])
            segs.append((x, x + w, it))
            x += w + fm.horizontalAdvance(SEP)
        self.segs, self.total = segs, max(x, 1)

    def tick(self):
        if not self.paused and self.segs:
            self.x = (self.x + self.speed * 0.016) % self.total
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.fillRect(self.rect(), QColor(14, 18, 26, self.alpha))
        mid = self.height() / 2
        if not self.segs:
            p.setPen(QColor("#cccccc")); p.setFont(self.font_)
            p.drawText(QRectF(10, 0, self.width() - 20, self.height()), Qt.AlignVCenter, self.status)
            return
        fm, fb = QFontMetrics(self.font_), QFontMetrics(self.font_b)
        sepw = fm.horizontalAdvance(SEP)
        base = mid + fm.ascent() / 2 - 2
        off = -self.x
        while off < self.width():                # repeat the strip to wrap seamlessly
            for x0, x1, it in self.segs:
                sx = off + x0
                if sx > self.width():
                    break
                if sx + (x1 - x0) + sepw < 0:
                    continue
                tag = f"[{it['cat']}] " if it["cat"] else ""
                p.setFont(self.font_b); p.setPen(QColor("#ffb86b"))
                p.drawText(int(sx), int(base), tag)
                p.setFont(self.font_); p.setPen(QColor("#f2f2f2"))
                p.drawText(int(sx + fb.horizontalAdvance(tag)), int(base), it["title"])
                p.setPen(QColor("#5ec8a0"))
                p.drawText(int(sx + (x1 - x0)), int(base), SEP)
            off += self.total
        p.end()

    def item_at(self, px):
        for k in (0, 1):
            pos = px + self.x - k * self.total
            for x0, x1, it in self.segs:
                if x0 <= pos <= x1:
                    return it
        return None

    def enterEvent(self, _): self.paused = True
    def leaveEvent(self, _): self.paused = False

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            it = self.item_at(e.position().x())
            if it and it["link"]:
                webbrowser.open(it["link"])

    def mouseMoveEvent(self, e):
        self.setCursor(Qt.PointingHandCursor if self.item_at(e.position().x()) else Qt.ArrowCursor)

    def contextMenuEvent(self, e):
        m = QMenu(self)
        def add(label, fn):
            a = QAction(label, m); a.triggered.connect(lambda _=False: fn()); m.addAction(a)
        add("Refresh now", self.refresh)
        add("Faster", lambda: self.set(speed=min(self.speed + 20, 300)))
        add("Slower", lambda: self.set(speed=max(self.speed - 20, 10)))
        add("Move to bottom" if self.at_top else "Move to top",
            lambda: self.set(top=not self.at_top))
        add("More opaque", lambda: self.set(alpha=min(self.alpha + 40, 255)))
        add("More transparent", lambda: self.set(alpha=max(self.alpha - 40, 0)))
        m.addSeparator()
        add("Open pollar.news", lambda: webbrowser.open("https://pollar.news/"))
        add("Quit", QApplication.quit)
        m.exec(e.globalPos())

    def set(self, **kw):
        self.speed = kw.get("speed", self.speed)
        self.alpha = kw.get("alpha", self.alpha)
        self.at_top = kw.get("top", self.at_top)
        self.cfg.update(speed=self.speed, alpha=self.alpha, top=self.at_top)
        save_cfg(self.cfg)
        self.place()


def main():
    ap = argparse.ArgumentParser(prog="pollar-ticker", description=__doc__)
    ap.add_argument("--feed", default=DEFAULT_FEED, help="RSS URL (e.g. https://pollar.news/de/feed.xml)")
    ap.add_argument("--refresh", type=int, default=5, help="refresh interval, minutes (min 2)")
    a = ap.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("pollar-ticker")
    app.setDesktopFileName("pollar-ticker")
    w = Ticker(a.feed, max(a.refresh, 2), load_cfg())
    w.show()
    sys.exit(app.exec())
