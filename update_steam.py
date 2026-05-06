import requests
import re
import os
from datetime import datetime

STEAM_ID = "76561198213538560"


def fetch_my_games(limit=5):
    api_key = os.environ["STEAM_API_KEY"]

    # tenta jogos recentes (últimas 2 semanas)
    resp = requests.get(
        "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/",
        params={"key": api_key, "steamid": STEAM_ID, "count": limit},
        timeout=10,
    )
    resp.raise_for_status()
    recent = resp.json().get("response", {}).get("games", [])

    if recent:
        top = sorted(recent, key=lambda g: g.get("playtime_2weeks", 0), reverse=True)[:limit]
        return [
            {"name": g["name"][:24], "playtime": g.get("playtime_2weeks", 0)}
            for g in top
        ], "recent"

    # fallback: todos os jogos ordenados por tempo total
    resp = requests.get(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
        params={
            "key": api_key,
            "steamid": STEAM_ID,
            "include_appinfo": 1,
            "include_played_free_games": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    owned = resp.json().get("response", {}).get("games", [])
    top = sorted(owned, key=lambda g: g.get("playtime_forever", 0), reverse=True)[:limit]

    return [
        {"name": g.get("name", f"AppID {g['appid']}")[:24], "playtime": g.get("playtime_forever", 0)}
        for g in top
    ], "alltime"


def format_playtime(minutes):
    if minutes >= 60:
        return f"{minutes // 60}h"
    return f"{minutes}m"


def bar_width(playtime, max_playtime, max_width=90):
    if max_playtime == 0:
        return 2
    return max(2, int((playtime / max_playtime) * max_width))


def generate_svg(games, source):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    max_playtime = max((g["playtime"] for g in games), default=1) or 1

    title = "Steam &#x2014; jogos recentes" if source == "recent" else "Steam &#x2014; mais jogados"

    rows = ""
    bar_colors = ["#3fb950", "#388bfd", "#388bfd", "#388bfd", "#388bfd"]
    text_colors = ["#3fb950", "#58a6ff", "#58a6ff", "#58a6ff", "#58a6ff"]

    for i, g in enumerate(games):
        y_text = 104 + i * 22
        y_bar = y_text - 8
        bw = bar_width(g["playtime"], max_playtime)
        rank_color = "#58a6ff" if i == 0 else "#8b949e"
        rank_weight = "700" if i == 0 else "400"
        rows += f'''
  <text x="44" y="{y_text}" font-family="monospace" font-size="11" fill="{rank_color}" font-weight="{rank_weight}">{i + 1}</text>
  <text x="68" y="{y_text}" font-family="monospace" font-size="11" fill="#e6edf3">{g["name"]}</text>
  <text x="440" y="{y_text}" font-family="monospace" font-size="11" fill="{text_colors[i]}" font-weight="600">{format_playtime(g["playtime"])}</text>
  <rect x="500" y="{y_bar}" width="90" height="8" rx="4" fill="#21262d"/>
  <rect x="500" y="{y_bar}" width="{bw}" height="8" rx="4" fill="{bar_colors[i]}"/>'''

    return f'''<svg width="100%" viewBox="0 0 680 255" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="16" width="640" height="223" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <rect x="20" y="16" width="640" height="44" rx="10" fill="#161b22"/>
  <rect x="20" y="44" width="640" height="16" fill="#161b22"/>
  <circle cx="44" cy="38" r="6" fill="#ff5f57"/>
  <circle cx="62" cy="38" r="6" fill="#febc2e"/>
  <circle cx="80" cy="38" r="6" fill="#28c840"/>
  <text x="340" y="43" text-anchor="middle" font-family="monospace" font-size="13" fill="#c9d1d9" font-weight="600">&#x1F3AE; {title}</text>
  <text x="44" y="80" font-family="monospace" font-size="10" fill="#8b949e">#</text>
  <text x="68" y="80" font-family="monospace" font-size="10" fill="#8b949e">JOGO</text>
  <text x="440" y="80" font-family="monospace" font-size="10" fill="#8b949e">HORAS</text>
  <text x="520" y="80" font-family="monospace" font-size="10" fill="#8b949e">DISTRIBUIÇÃO</text>
  <line x1="40" y1="86" x2="640" y2="86" stroke="#30363d" stroke-width="0.8"/>
  {rows}
  <line x1="40" y1="208" x2="640" y2="208" stroke="#30363d" stroke-width="0.8"/>
  <text x="44" y="225" font-family="monospace" font-size="9" fill="#6e7681">Steam API + Python + GitHub Actions</text>
  <text x="636" y="225" text-anchor="end" font-family="monospace" font-size="9" fill="#6e7681">atualizado: {now}</text>
</svg>'''


def update_readme(svg_filename="steam-live.svg"):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    block = f"<!-- STEAM_LIVE_START -->\n![Steam Live]({svg_filename})\n<!-- STEAM_LIVE_END -->"
    pattern = r"<!-- STEAM_LIVE_START -->.*?<!-- STEAM_LIVE_END -->"

    if re.search(pattern, content, flags=re.DOTALL):
        updated = re.sub(pattern, block, content, flags=re.DOTALL)
    else:
        updated = content + "\n\n" + block

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)


if __name__ == "__main__":
    print("Buscando jogos do perfil Steam...")
    games, source = fetch_my_games(limit=5)
    label = "recentes (2 semanas)" if source == "recent" else "mais jogados (all time)"
    print(f"  Fonte: {label}")
    for g in games:
        print(f"  {g['name']} — {format_playtime(g['playtime'])}")

    svg = generate_svg(games, source)
    with open("steam-live.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("steam-live.svg gerado.")

    update_readme("steam-live.svg")
    print("README.md atualizado.")
