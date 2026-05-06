import requests
import re
from datetime import datetime


def fetch_top_steam_games(limit=5):
    url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    games = data.get("response", {}).get("ranks", [])[:limit]

    results = []
    for game in games:
        appid = game["appid"]
        players = game.get("concurrent_in_game") or game.get("peak_in_game", 0)

        name_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic"
        try:
            name_resp = requests.get(name_url, timeout=8)
            name_data = name_resp.json()
            name = name_data[str(appid)]["data"]["name"]
        except Exception:
            name = f"AppID {appid}"

        results.append({"name": name, "players": players})

    return results


def format_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}k"
    return str(n)


def build_section(games):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    lines = ["<!-- STEAM_LIVE_START -->"]
    lines.append("## 🎮 Steam Live — Top jogos agora")
    lines.append("```")
    lines.append(f"{'#':<4} {'Jogo':<35} {'Jogadores'}")
    lines.append("─" * 52)
    for i, g in enumerate(games, 1):
        name = g["name"][:34]
        players = format_number(g["players"])
        lines.append(f"{i:<4} {name:<35} {players}")
    lines.append("─" * 52)
    lines.append(f"⚙️  Steam API + Python + GitHub Actions · {now}")
    lines.append("```")
    lines.append("<!-- STEAM_LIVE_END -->")
    return "\n".join(lines)


def update_readme(section):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- STEAM_LIVE_START -->.*?<!-- STEAM_LIVE_END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        updated = re.sub(pattern, section, content, flags=re.DOTALL)
    else:
        updated = content + "\n\n" + section

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)

    print("README.md atualizado com sucesso.")


if __name__ == "__main__":
    print("Buscando top jogos da Steam...")
    games = fetch_top_steam_games(limit=5)
    for g in games:
        print(f"  {g['name']} — {format_number(g['players'])} jogadores")
    section = build_section(games)
    update_readme(section)
