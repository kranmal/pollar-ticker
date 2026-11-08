# pollar-ticker

Scrolling desktop news ticker for [Pollar](https://pollar.news/en), built on its public RSS feed.
A slim always-on-top bar at the top of your screen (default 700 px wide, centred). Headlines scroll continuously.

![pollar-ticker screenshot](docs/screenshot.png)

## Features
- Live headlines with category tag, refreshed every 5 minutes
- Hover pauses scrolling; click a headline to open it in your browser
- Drag anywhere to move; drag the left/right/bottom edge to resize (text scales with height); position and size are remembered
- Right-click menu: refresh, speed, opacity, snap top/bottom, reset size, open pollar.news, quit
- Settings remembered in `~/.config/pollar-ticker/config.json`
- Other Pollar languages via `--feed`, e.g. `pollar-ticker --feed https://pollar.news/de/feed.xml`

## Install

    git clone https://github.com/kranmal/pollar-ticker && cd pollar-ticker
    ./install.sh        # or: pipx install .

Run `pollar-ticker`. Autostart: copy `data/pollar-ticker.desktop` to `~/.config/autostart/`.

Options: `--feed URL`, `--refresh MINUTES` (min 2).

Requires Linux, Python >= 3.9, PySide6 (installed automatically).
Uninstall: `pipx uninstall pollar-ticker`.

## Notes
- Uses only the public RSS feed (`/en/feed.xml`); the `/api/` paths that Pollar's robots.txt disallows are not used.
- Pollar headlines and summaries are AI-generated; each item links back to the source page on pollar.news.
- Unofficial project, not affiliated with Pollar.
- Wayland: window stacking/positioning depends on the compositor; X11/XWayland is most reliable.

MIT licensed.
