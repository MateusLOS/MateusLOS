import requests
import re
from datetime import datetime

def fetch_top_steam_games(limit=5):
    url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    games = response.json().get("response", {}).get("ranks", [])[:limit]

    results = []
    for game in games:
        appid = game["appid"]
        players = game.get("concurrent_in_game") or game.get("peak_in_game", 0)
        try:
            name_resp = requests.get(
                f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic",
                timeout=8
            )
            name = name_resp.json()[str(appid)]["data"]["name"]
        except Exception:
            name = f"AppID {appid}"
        results.append({"name": name[:22], "players": players})

    return results

def format_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}k"
    return str(n)

def bar_width(players, max_players, max_width=90):
    if max_players == 0:
        return 2
    return max(2, int((players / max_players) * max_width))

def generate_svg(games):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    max_players = max(g["players"] for g in games) if games else 1

    rows = ""
    colors = ["#3fb950", "#388bfd", "#388bfd", "#388bfd", "#388bfd"]
    player_colors = ["#3fb950", "#58a6ff", "#58a6ff", "#58a6ff", "#58a6ff"]

    for i, g in enumerate(games):
        y_text = 104 + i * 22
        y_bar = y_text - 8
        bw = bar_width(g["players"], max_players)
        rank_color = "#58a6ff" if i == 0 else "#8b949e"
        rank_weight = "700" if i == 0 else "400"
        rows += f'''
  <text x="44" y="{y_text}" font-family="monospace" font-size="11" fill="{rank_color}" font-weight="{rank_weight}">{i+1}</text>
  <text x="68" y="{y_text}" font-family="monospace" font-size="11" fill="#e6edf3">{g["name"]}</text>
  <text x="440" y="{y_text}" font-family="monospace" font-size="11" fill="{player_colors[i]}" font-weight="600">{format_number(g["players"])}</text>
  <rect x="540" y="{y_bar}" width="90" height="8" rx="4" fill="#21262d"/>
  <rect x="540" y="{y_bar}" width="{bw}" height="8" rx="4" fill="{colors[i]}"/>'''

    svg = f'''<svg width="100%" viewBox="0 0 680 255" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="16" width="640" height="223" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <rect x="20" y="16" width="640" height="44" rx="10" fill="#161b22"/>
  <rect x="20" y="44" width="640" height="16" fill="#161b22"/>
  <circle cx="44" cy="38" r="6" fill="#ff5f57"/>
  <circle cx="62" cy="38" r="6" fill="#febc2e"/>
  <circle cx="80" cy="38" r="6" fill="#28c840"/>
  <text x="340" y="43" text-anchor="middle" font-family="monospace" font-size="13" fill="#c9d1d9" font-weight="600">&#x1F3AE; Steam Live &#x2014; top jogos agora</text>
  <text x="44" y="80" font-family="monospace" font-size="10" fill="#8b949e">#</text>
  <text x="68" y="80" font-family="monospace" font-size="10" fill="#8b949e">JOGO</text>
  <text x="440" y="80" font-family="monospace" font-size="10" fill="#8b949e">JOGADORES</text>
  <text x="560" y="80" font-family="monospace" font-size="10" fill="#8b949e">DISTRIBUICAO</text>
  <line x1="40" y1="86" x2="640" y2="86" stroke="#30363d" stroke-width="0.8"/>
  {rows}
  <line x1="40" y1="208" x2="640" y2="208" stroke="#30363d" stroke-width="0.8"/>
  <text x="44" y="225" font-family="monospace" font-size="9" fill="#6e7681">Steam API + Python + GitHub Actions</text>
  <text x="636" y="225" text-anchor="end" font-family="monospace" font-size="9" fill="#6e7681">atualizado: {now}</text>
</svg>'''
    return svg

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
    print("Buscando top jogos da Steam...")
    games = fetch_top_steam_games(limit=5)
    for g in games:
        print(f"  {g['name']} — {format_number(g['players'])} jogadores")

    svg = generate_svg(games)
    with open("steam-live.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("steam-live.svg gerado.")

    update_readme("steam-live.svg")
    print("README.md atualizado.")
