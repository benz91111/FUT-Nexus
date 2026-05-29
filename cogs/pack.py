import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sqlite3
import os
import aiohttp
from datetime import datetime

# ============ CONFIGURAÇOES ============
RARITY_CONFIG = {
    "Comum": {"color": 0x95a5a6, "emoji": "⚪", "weight": 60, "min_ovr": 65, "max_ovr": 74},
    "Raro": {"color": 0x3498db, "emoji": "🔵", "weight": 25, "min_ovr": 75, "max_ovr": 81},
    "Epico": {"color": 0x9b59b6, "emoji": "🟣", "weight": 10, "min_ovr": 82, "max_ovr": 86},
    "Lendario": {"color": 0xf1c40f, "emoji": "🟡", "weight": 4, "min_ovr": 87, "max_ovr": 91},
    "Icone": {"color": 0xe74c3c, "emoji": "🔴", "weight": 1, "min_ovr": 92, "max_ovr": 99}
}

# ============ DATABASE ============
def get_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/players.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            player_nation TEXT,
            player_position TEXT,
            player_club TEXT,
            overall INTEGER,
            rarity TEXT,
            image_url TEXT,
            rolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS roll_cooldown (
            user_id TEXT PRIMARY KEY,
            last_roll TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ============ JOGADORES DA COPA 2026 ============
# Fotos do Transfermarkt com IDs verificados

def tm_url(player_id):
    return f"https://img.a.transfermarkt.technology/portrait/header/{player_id}.jpg"

PLAYERS = [
    # ICONES (OVR 92-99)
    {"name": "Lionel Messi", "nation": "Argentina", "position": "ATA", "club": "Inter Miami", "rarity": "Icone", "overall": 95, "tm_id": "28003"},
    {"name": "Cristiano Ronaldo", "nation": "Portugal", "position": "ATA", "club": "Al Nassr", "rarity": "Icone", "overall": 93, "tm_id": "8198"},
    {"name": "Neymar Jr", "nation": "Brasil", "position": "ATA", "club": "Al Hilal", "rarity": "Icone", "overall": 92, "tm_id": "68290"},
    {"name": "Kylian Mbappe", "nation": "Franca", "position": "ATA", "club": "Real Madrid", "rarity": "Icone", "overall": 97, "tm_id": "342229"},
    {"name": "Erling Haaland", "nation": "Noruega", "position": "ATA", "club": "Manchester City", "rarity": "Icone", "overall": 96, "tm_id": "418560"},

    # LENDARIOS (OVR 87-91)
    {"name": "Vinicius Jr", "nation": "Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Lendario", "overall": 91, "tm_id": "371998"},
    {"name": "Jude Bellingham", "nation": "Inglaterra", "position": "MC", "club": "Real Madrid", "rarity": "Lendario", "overall": 90, "tm_id": "581678"},
    {"name": "Rodri", "nation": "Espanha", "position": "VOL", "club": "Manchester City", "rarity": "Lendario", "overall": 90, "tm_id": "357565"},
    {"name": "Phil Foden", "nation": "Inglaterra", "position": "ME", "club": "Manchester City", "rarity": "Lendario", "overall": 89, "tm_id": "406635"},
    {"name": "Bukayo Saka", "nation": "Inglaterra", "position": "PD", "club": "Arsenal", "rarity": "Lendario", "overall": 89, "tm_id": "433177"},
    {"name": "Jamal Musiala", "nation": "Alemanha", "position": "ME", "club": "Bayern Munich", "rarity": "Lendario", "overall": 88, "tm_id": "580195"},
    {"name": "Florian Wirtz", "nation": "Alemanha", "position": "ME", "club": "Bayer Leverkusen", "rarity": "Lendario", "overall": 88, "tm_id": "598577"},
    {"name": "Lamine Yamal", "nation": "Espanha", "position": "PD", "club": "Barcelona", "rarity": "Lendario", "overall": 87, "tm_id": "937958"},
    {"name": "Pedri", "nation": "Espanha", "position": "MC", "club": "Barcelona", "rarity": "Lendario", "overall": 87, "tm_id": "683840"},
    {"name": "Endrick", "nation": "Brasil", "position": "ATA", "club": "Real Madrid", "rarity": "Lendario", "overall": 87, "tm_id": "987128"},

    # EPICOS (OVR 82-86)
    {"name": "Federico Valverde", "nation": "Uruguai", "position": "MC", "club": "Real Madrid", "rarity": "Epico", "overall": 86, "tm_id": "369081"},
    {"name": "Enzo Fernandez", "nation": "Argentina", "position": "MC", "club": "Chelsea", "rarity": "Epico", "overall": 86, "tm_id": "648195"},
    {"name": "Alexis Mac Allister", "nation": "Argentina", "position": "MC", "club": "Liverpool", "rarity": "Epico", "overall": 85, "tm_id": "534033"},
    {"name": "Declan Rice", "nation": "Inglaterra", "position": "VOL", "club": "Arsenal", "rarity": "Epico", "overall": 85, "tm_id": "357662"},
    {"name": "Bruno Guimaraes", "nation": "Brasil", "position": "MC", "club": "Newcastle", "rarity": "Epico", "overall": 85, "tm_id": "520624"},
    {"name": "Rodrygo", "nation": "Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Epico", "overall": 84, "tm_id": "412363"},
    {"name": "Gavi", "nation": "Espanha", "position": "MC", "club": "Barcelona", "rarity": "Epico", "overall": 84, "tm_id": "646740"},
    {"name": "Khvicha Kvaratskhelia", "nation": "Georgia", "position": "PE", "club": "PSG", "rarity": "Epico", "overall": 83, "tm_id": "502670"},
    {"name": "William Saliba", "nation": "Franca", "position": "ZAG", "club": "Arsenal", "rarity": "Epico", "overall": 83, "tm_id": "495666"},
    {"name": "Rafael Leao", "nation": "Portugal", "position": "PE", "club": "AC Milan", "rarity": "Epico", "overall": 82, "tm_id": "357164"},
    {"name": "Victor Osimhen", "nation": "Nigeria", "position": "ATA", "club": "Galatasaray", "rarity": "Epico", "overall": 82, "tm_id": "401923"},
    {"name": "Kai Havertz", "nation": "Alemanha", "position": "ATA", "club": "Arsenal", "rarity": "Epico", "overall": 82, "tm_id": "309400"},

    # RAROS (OVR 75-81)
    {"name": "Julian Alvarez", "nation": "Argentina", "position": "ATA", "club": "Atletico Madrid", "rarity": "Raro", "overall": 81, "tm_id": "576024"},
    {"name": "Nicolas Jackson", "nation": "Senegal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 80, "tm_id": "503275"},
    {"name": "Cole Palmer", "nation": "Inglaterra", "position": "ME", "club": "Chelsea", "rarity": "Raro", "overall": 80, "tm_id": "559371"},
    {"name": "Gabriel Martinelli", "nation": "Brasil", "position": "PE", "club": "Arsenal", "rarity": "Raro", "overall": 79, "tm_id": "653052"},
    {"name": "Martin Odegaard", "nation": "Noruega", "position": "ME", "club": "Arsenal", "rarity": "Raro", "overall": 79, "tm_id": "316264"},
    {"name": "Diogo Jota", "nation": "Portugal", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "tm_id": "340950"},
    {"name": "Darwin Nunez", "nation": "Uruguai", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "tm_id": "546543"},
    {"name": "Christopher Nkunku", "nation": "Franca", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 77, "tm_id": "344381"},
    {"name": "Dominik Szoboszlai", "nation": "Hungria", "position": "MC", "club": "Liverpool", "rarity": "Raro", "overall": 77, "tm_id": "451276"},
    {"name": "Joao Felix", "nation": "Portugal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 76, "tm_id": "462250"},
    {"name": "Georginio Rutter", "nation": "Franca", "position": "ATA", "club": "Brighton", "rarity": "Raro", "overall": 76, "tm_id": "567441"},
    {"name": "Micky van de Ven", "nation": "Holanda", "position": "ZAG", "club": "Tottenham", "rarity": "Raro", "overall": 75, "tm_id": "597158"},
    {"name": "Jeremy Doku", "nation": "Belgica", "position": "PE", "club": "Manchester City", "rarity": "Raro", "overall": 75, "tm_id": "486049"},
    {"name": "Benjamin Sesko", "nation": "Eslovenia", "position": "ATA", "club": "RB Leipzig", "rarity": "Raro", "overall": 75, "tm_id": "627495"},

    # COMUNS (OVR 65-74)
    {"name": "Conor Gallagher", "nation": "Inglaterra", "position": "MC", "club": "Atletico Madrid", "rarity": "Comum", "overall": 74, "tm_id": "488404"},
    {"name": "Morgan Rogers", "nation": "Inglaterra", "position": "ME", "club": "Aston Villa", "rarity": "Comum", "overall": 73, "tm_id": "477558"},
    {"name": "Dejan Kulusevski", "nation": "Suecia", "position": "PD", "club": "Tottenham", "rarity": "Comum", "overall": 73, "tm_id": "413235"},
    {"name": "Brennan Johnson", "nation": "Pais de Gales", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 72, "tm_id": "503276"},
    {"name": "Morgan Gibbs-White", "nation": "Inglaterra", "position": "ME", "club": "Nottingham Forest", "rarity": "Comum", "overall": 72, "tm_id": "434324"},
    {"name": "Anthony Gordon", "nation": "Inglaterra", "position": "PE", "club": "Newcastle", "rarity": "Comum", "overall": 71, "tm_id": "503275"},
    {"name": "Curtis Jones", "nation": "Inglaterra", "position": "MC", "club": "Liverpool", "rarity": "Comum", "overall": 71, "tm_id": "405265"},
    {"name": "Eberechi Eze", "nation": "Inglaterra", "position": "ME", "club": "Crystal Palace", "rarity": "Comum", "overall": 70, "tm_id": "424876"},
    {"name": "Dominic Solanke", "nation": "Inglaterra", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 70, "tm_id": "346472"},
    {"name": "Jarrod Bowen", "nation": "Inglaterra", "position": "PD", "club": "West Ham", "rarity": "Comum", "overall": 69, "tm_id": "326763"},
    {"name": "James Ward-Prowse", "nation": "Inglaterra", "position": "MC", "club": "West Ham", "rarity": "Comum", "overall": 69, "tm_id": "156689"},
    {"name": "Pedro Neto", "nation": "Portugal", "position": "PE", "club": "Chelsea", "rarity": "Comum", "overall": 68, "tm_id": "495666"},
    {"name": "Joao Pedro", "nation": "Brasil", "position": "ATA", "club": "Brighton", "rarity": "Comum", "overall": 68, "tm_id": "645277"},
    {"name": "Matheus Cunha", "nation": "Brasil", "position": "ATA", "club": "Wolves", "rarity": "Comum", "overall": 67, "tm_id": "534033"},
    {"name": "Trent Alexander-Arnold", "nation": "Inglaterra", "position": "LD", "club": "Liverpool", "rarity": "Comum", "overall": 66, "tm_id": "314353"},
    {"name": "Lisandro Martinez", "nation": "Argentina", "position": "ZAG", "club": "Manchester United", "rarity": "Comum", "overall": 66, "tm_id": "482488"},
    {"name": "Alejandro Garnacho", "nation": "Argentina", "position": "PE", "club": "Manchester United", "rarity": "Comum", "overall": 65, "tm_id": "668049"},
    {"name": "Kobbie Mainoo", "nation": "Inglaterra", "position": "MC", "club": "Manchester United", "rarity": "Comum", "overall": 65, "tm_id": "686578"},
]

# Agrupar por raridade
PLAYERS_BY_RARITY = {}
for p in PLAYERS:
    r = p["rarity"]
    if r not in PLAYERS_BY_RARITY:
        PLAYERS_BY_RARITY[r] = []
    PLAYERS_BY_RARITY[r].append(p)

def roll_rarity():
    rarities = list(RARITY_CONFIG.keys())
    weights = [RARITY_CONFIG[r]["weight"] for r in rarities]
    return random.choices(rarities, weights=weights, k=1)[0]

def roll_player():
    rarity = roll_rarity()
    player = random.choice(PLAYERS_BY_RARITY[rarity])
    return player

async def download_player_image(tm_id, player_name):
    """Baixa a foto do jogador do Transfermarkt"""
    cache_dir = "assets/players"
    os.makedirs(cache_dir, exist_ok=True)

    cache_file = os.path.join(cache_dir, f"{tm_id}.jpg")

    # Se ja existe no cache, retorna
    if os.path.exists(cache_file):
        return cache_file

    # Tenta baixar do Transfermarkt
    urls = [
        f"https://img.a.transfermarkt.technology/portrait/header/{tm_id}.jpg",
        f"https://img.a.transfermarkt.technology/portrait/header/{tm_id}-1700653093.jpg",
        f"https://img.a.transfermarkt.technology/portrait/header/{tm_id}-1716899475.jpg",
    ]

    for url in urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 1000:  # Verifica se nao eh imagem vazia
                            with open(cache_file, "wb") as f:
                                f.write(data)
                            return cache_file
        except Exception:
            continue

    return None

# ============ COG ============
class PackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_seconds = 30

    @app_commands.command(name="roll", description="Abre um pacote e revela um jogador da Copa 2026!")
    async def roll(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT last_roll FROM roll_cooldown WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if row:
            last_roll = datetime.fromisoformat(row["last_roll"])
            elapsed = (datetime.now() - last_roll).total_seconds()
            if elapsed < self.cooldown_seconds:
                remaining = int(self.cooldown_seconds - elapsed)
                await interaction.response.send_message(
                    f"⏳ Calma ai! Espera **{remaining}s** pra abrir outro pacote.",
                    ephemeral=True
                )
                conn.close()
                return

        await interaction.response.defer()

        embed = discord.Embed(
            title="🎁 ABRINDO PACOTE...",
            description="Preparando seu pack da Copa 2026...",
            color=0xFFD700
        )
        msg = await interaction.followup.send(embed=embed)

        await asyncio.sleep(1.5)

        player = roll_player()
        config = RARITY_CONFIG[player["rarity"]]

        # Baixar foto do jogador
        image_path = await download_player_image(player["tm_id"], player["name"])

        # Salvar no banco
        image_url = f"https://img.a.transfermarkt.technology/portrait/header/{player['tm_id']}.jpg" if image_path else ""
        c.execute("""
            INSERT INTO user_players (user_id, player_name, player_nation, player_position, player_club, overall, rarity, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, player["name"], player["nation"], player["position"], 
              player["club"], player["overall"], player["rarity"], image_url))

        c.execute("""
            INSERT OR REPLACE INTO roll_cooldown (user_id, last_roll)
            VALUES (?, ?)
        """, (user_id, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Criar embed
        embed = discord.Embed(
            title=f"{config['emoji']} {player['rarity'].upper()}!",
            description=f"**{player['name']}** entrou pro seu time!",
            color=config["color"]
        )
        embed.add_field(name="🌍 Nacao", value=player["nation"], inline=True)
        embed.add_field(name="⚽ Posicao", value=player["position"], inline=True)
        embed.add_field(name="🏟️ Clube", value=player["club"], inline=True)
        embed.add_field(name="⭐ Overall", value=f"**{player['overall']}**", inline=True)
        embed.set_footer(text=f"Pack aberto por {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        # Se conseguiu baixar a foto, anexa
        if image_path and os.path.exists(image_path):
            file = discord.File(image_path, filename="player.jpg")
            embed.set_image(url="attachment://player.jpg")
            await msg.edit(embed=embed, attachments=[file])
        else:
            await msg.edit(embed=embed)

    @app_commands.command(name="probabilidades", description="Ver as chances de cada raridade")
    async def probabilidades(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📊 Probabilidades dos Packs",
            description="Quanto mais raro, mais dificil de cair!",
            color=0xFFD700
        )

        for rarity, config in RARITY_CONFIG.items():
            total_players = len(PLAYERS_BY_RARITY.get(rarity, []))
            embed.add_field(
                name=f"{config['emoji']} {rarity}",
                value=f"Chance: **{config['weight']}%**\nJogadores: **{total_players}**\nOVR: {config['min_ovr']}-{config['max_ovr']}",
                inline=True
            )

        embed.set_footer(text="Boa sorte nos seus rolls! 🍀")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PackCog(bot))
