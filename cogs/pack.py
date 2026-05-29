import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sqlite3
import os
from datetime import datetime

# ============ CONFIGURAÇÕES ============
RARITY_CONFIG = {
    "Comum": {"color": 0x95a5a6, "emoji": "⚪", "weight": 60, "min_ovr": 65, "max_ovr": 74},
    "Raro": {"color": 0x3498db, "emoji": "🔵", "weight": 25, "min_ovr": 75, "max_ovr": 81},
    "Épico": {"color": 0x9b59b6, "emoji": "🟣", "weight": 10, "min_ovr": 82, "max_ovr": 86},
    "Lendário": {"color": 0xf1c40f, "emoji": "🟡", "weight": 4, "min_ovr": 87, "max_ovr": 91},
    "Ícone": {"color": 0xe74c3c, "emoji": "🔴", "weight": 1, "min_ovr": 92, "max_ovr": 99}
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

# ============ JOGADORES DA COPA 2026 - FOTOS FUTBIN ============
PLAYERS = [
    # ÍCONES (OVR 92-99)
    {"name": "Lionel Messi", "nation": "🇦🇷 Argentina", "position": "ATA", "club": "Inter Miami", "rarity": "Ícone", "overall": 95, "image": "https://cdn.futbin.com/content/fifa25/img/players/158023.png"},
    {"name": "Cristiano Ronaldo", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Al Nassr", "rarity": "Ícone", "overall": 93, "image": "https://cdn.futbin.com/content/fifa25/img/players/20801.png"},
    {"name": "Neymar Jr", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Al Hilal", "rarity": "Ícone", "overall": 92, "image": "https://cdn.futbin.com/content/fifa25/img/players/190871.png"},
    {"name": "Kylian Mbappé", "nation": "🇫🇷 França", "position": "ATA", "club": "Real Madrid", "rarity": "Ícone", "overall": 97, "image": "https://cdn.futbin.com/content/fifa25/img/players/231747.png"},
    {"name": "Erling Haaland", "nation": "🇳🇴 Noruega", "position": "ATA", "club": "Manchester City", "rarity": "Ícone", "overall": 96, "image": "https://cdn.futbin.com/content/fifa25/img/players/239085.png"},
    
    # LENDÁRIOS (OVR 87-91)
    {"name": "Vinicius Jr", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Lendário", "overall": 91, "image": "https://cdn.futbin.com/content/fifa25/img/players/238794.png"},
    {"name": "Jude Bellingham", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Real Madrid", "rarity": "Lendário", "overall": 90, "image": "https://cdn.futbin.com/content/fifa25/img/players/252371.png"},
    {"name": "Rodri", "nation": "🇪🇸 Espanha", "position": "VOL", "club": "Manchester City", "rarity": "Lendário", "overall": 90, "image": "https://cdn.futbin.com/content/fifa25/img/players/216267.png"},
    {"name": "Phil Foden", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Manchester City", "rarity": "Lendário", "overall": 89, "image": "https://cdn.futbin.com/content/fifa25/img/players/231866.png"},
    {"name": "Bukayo Saka", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PD", "club": "Arsenal", "rarity": "Lendário", "overall": 89, "image": "https://cdn.futbin.com/content/fifa25/img/players/246669.png"},
    {"name": "Jamal Musiala", "nation": "🇩🇪 Alemanha", "position": "ME", "club": "Bayern Munich", "rarity": "Lendário", "overall": 88, "image": "https://cdn.futbin.com/content/fifa25/img/players/256790.png"},
    {"name": "Florian Wirtz", "nation": "🇩🇪 Alemanha", "position": "ME", "club": "Bayer Leverkusen", "rarity": "Lendário", "overall": 88, "image": "https://cdn.futbin.com/content/fifa25/img/players/258948.png"},
    {"name": "Lamine Yamal", "nation": "🇪🇸 Espanha", "position": "PD", "club": "Barcelona", "rarity": "Lendário", "overall": 87, "image": "https://cdn.futbin.com/content/fifa25/img/players/264240.png"},
    {"name": "Pedri", "nation": "🇪🇸 Espanha", "position": "MC", "club": "Barcelona", "rarity": "Lendário", "overall": 87, "image": "https://cdn.futbin.com/content/fifa25/img/players/251854.png"},
    {"name": "Endrick", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Real Madrid", "rarity": "Lendário", "overall": 87, "image": "https://cdn.futbin.com/content/fifa25/img/players/264657.png"},
    
    # ÉPICOS (OVR 82-86)
    {"name": "Federico Valverde", "nation": "🇺🇾 Uruguai", "position": "MC", "club": "Real Madrid", "rarity": "Épico", "overall": 86, "image": "https://cdn.futbin.com/content/fifa25/img/players/239053.png"},
    {"name": "Enzo Fernández", "nation": "🇦🇷 Argentina", "position": "MC", "club": "Chelsea", "rarity": "Épico", "overall": 86, "image": "https://cdn.futbin.com/content/fifa25/img/players/264035.png"},
    {"name": "Alexis Mac Allister", "nation": "🇦🇷 Argentina", "position": "MC", "club": "Liverpool", "rarity": "Épico", "overall": 85, "image": "https://cdn.futbin.com/content/fifa25/img/players/232730.png"},
    {"name": "Declan Rice", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "VOL", "club": "Arsenal", "rarity": "Épico", "overall": 85, "image": "https://cdn.futbin.com/content/fifa25/img/players/234378.png"},
    {"name": "Bruno Guimarães", "nation": "🇧🇷 Brasil", "position": "MC", "club": "Newcastle", "rarity": "Épico", "overall": 85, "image": "https://cdn.futbin.com/content/fifa25/img/players/247851.png"},
    {"name": "Rodrygo", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Épico", "overall": 84, "image": "https://cdn.futbin.com/content/fifa25/img/players/243812.png"},
    {"name": "Gavi", "nation": "🇪🇸 Espanha", "position": "MC", "club": "Barcelona", "rarity": "Épico", "overall": 84, "image": "https://cdn.futbin.com/content/fifa25/img/players/264240.png"},
    {"name": "Khvicha Kvaratskhelia", "nation": "🇬🇪 Geórgia", "position": "PE", "club": "PSG", "rarity": "Épico", "overall": 83, "image": "https://cdn.futbin.com/content/fifa25/img/players/256507.png"},
    {"name": "William Saliba", "nation": "🇫🇷 França", "position": "ZAG", "club": "Arsenal", "rarity": "Épico", "overall": 83, "image": "https://cdn.futbin.com/content/fifa25/img/players/243715.png"},
    {"name": "Rafael Leão", "nation": "🇵🇹 Portugal", "position": "PE", "club": "AC Milan", "rarity": "Épico", "overall": 82, "image": "https://cdn.futbin.com/content/fifa25/img/players/241651.png"},
    {"name": "Victor Osimhen", "nation": "🇳🇬 Nigéria", "position": "ATA", "club": "Galatasaray", "rarity": "Épico", "overall": 82, "image": "https://cdn.futbin.com/content/fifa25/img/players/232293.png"},
    {"name": "Kai Havertz", "nation": "🇩🇪 Alemanha", "position": "ATA", "club": "Arsenal", "rarity": "Épico", "overall": 82, "image": "https://cdn.futbin.com/content/fifa25/img/players/233419.png"},
    
    # RAROS (OVR 75-81)
    {"name": "Julian Alvarez", "nation": "🇦🇷 Argentina", "position": "ATA", "club": "Atletico Madrid", "rarity": "Raro", "overall": 81, "image": "https://cdn.futbin.com/content/fifa25/img/players/246669.png"},
    {"name": "Nicolas Jackson", "nation": "🇸🇳 Senegal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 80, "image": "https://cdn.futbin.com/content/fifa25/img/players/264240.png"},
    {"name": "Cole Palmer", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Chelsea", "rarity": "Raro", "overall": 80, "image": "https://cdn.futbin.com/content/fifa25/img/players/256790.png"},
    {"name": "Gabriel Martinelli", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Arsenal", "rarity": "Raro", "overall": 79, "image": "https://cdn.futbin.com/content/fifa25/img/players/251854.png"},
    {"name": "Martin Ødegaard", "nation": "🇳🇴 Noruega", "position": "ME", "club": "Arsenal", "rarity": "Raro", "overall": 79, "image": "https://cdn.futbin.com/content/fifa25/img/players/222665.png"},
    {"name": "Diogo Jota", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "image": "https://cdn.futbin.com/content/fifa25/img/players/224293.png"},
    {"name": "Darwin Núñez", "nation": "🇺🇾 Uruguai", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "image": "https://cdn.futbin.com/content/fifa25/img/players/253072.png"},
    {"name": "Christopher Nkunku", "nation": "🇫🇷 França", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 77, "image": "https://cdn.futbin.com/content/fifa25/img/players/232669.png"},
    {"name": "Dominik Szoboszlai", "nation": "🇭🇺 Hungria", "position": "MC", "club": "Liverpool", "rarity": "Raro", "overall": 77, "image": "https://cdn.futbin.com/content/fifa25/img/players/236583.png"},
    {"name": "João Félix", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 76, "image": "https://cdn.futbin.com/content/fifa25/img/players/242444.png"},
    {"name": "Georginio Rutter", "nation": "🇫🇷 França", "position": "ATA", "club": "Brighton", "rarity": "Raro", "overall": 76, "image": "https://cdn.futbin.com/content/fifa25/img/players/256507.png"},
    {"name": "Micky van de Ven", "nation": "🇳🇱 Holanda", "position": "ZAG", "club": "Tottenham", "rarity": "Raro", "overall": 75, "image": "https://cdn.futbin.com/content/fifa25/img/players/258948.png"},
    {"name": "Jeremy Doku", "nation": "🇧🇪 Bélgica", "position": "PE", "club": "Manchester City", "rarity": "Raro", "overall": 75, "image": "https://cdn.futbin.com/content/fifa25/img/players/252371.png"},
    {"name": "Benjamin Sesko", "nation": "🇸🇮 Eslovênia", "position": "ATA", "club": "RB Leipzig", "rarity": "Raro", "overall": 75, "image": "https://cdn.futbin.com/content/fifa25/img/players/258948.png"},
    
    # COMUNS (OVR 65-74)
    {"name": "Conor Gallagher", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Atletico Madrid", "rarity": "Comum", "overall": 74, "image": "https://cdn.futbin.com/content/fifa25/img/players/232669.png"},
    {"name": "Morgan Rogers", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Aston Villa", "rarity": "Comum", "overall": 73, "image": "https://cdn.futbin.com/content/fifa25/img/players/264240.png"},
    {"name": "Dejan Kulusevski", "nation": "🇸🇪 Suécia", "position": "PD", "club": "Tottenham", "rarity": "Comum", "overall": 73, "image": "https://cdn.futbin.com/content/fifa25/img/players/247851.png"},
    {"name": "Brennan Johnson", "nation": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 72, "image": "https://cdn.futbin.com/content/fifa25/img/players/256507.png"},
    {"name": "Morgan Gibbs-White", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Nottingham Forest", "rarity": "Comum", "overall": 72, "image": "https://cdn.futbin.com/content/fifa25/img/players/258948.png"},
    {"name": "Anthony Gordon", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PE", "club": "Newcastle", "rarity": "Comum", "overall": 71, "image": "https://cdn.futbin.com/content/fifa25/img/players/252371.png"},
    {"name": "Curtis Jones", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Liverpool", "rarity": "Comum", "overall": 71, "image": "https://cdn.futbin.com/content/fifa25/img/players/232730.png"},
    {"name": "Eberechi Eze", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Crystal Palace", "rarity": "Comum", "overall": 70, "image": "https://cdn.futbin.com/content/fifa25/img/players/258948.png"},
    {"name": "Dominic Solanke", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 70, "image": "https://cdn.futbin.com/content/fifa25/img/players/232293.png"},
    {"name": "Jarrod Bowen", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PD", "club": "West Ham", "rarity": "Comum", "overall": 69, "image": "https://cdn.futbin.com/content/fifa25/img/players/243812.png"},
    {"name": "James Ward-Prowse", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "West Ham", "rarity": "Comum", "overall": 69, "image": "https://cdn.futbin.com/content/fifa25/img/players/216267.png"},
    {"name": "Pedro Neto", "nation": "🇵🇹 Portugal", "position": "PE", "club": "Chelsea", "rarity": "Comum", "overall": 68, "image": "https://cdn.futbin.com/content/fifa25/img/players/247851.png"},
    {"name": "João Pedro", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Brighton", "rarity": "Comum", "overall": 68, "image": "https://cdn.futbin.com/content/fifa25/img/players/264240.png"},
    {"name": "Matheus Cunha", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Wolves", "rarity": "Comum", "overall": 67, "image": "https://cdn.futbin.com/content/fifa25/img/players/258948.png"},
    {"name": "Trent Alexander-Arnold", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "LD", "club": "Liverpool", "rarity": "Comum", "overall": 66, "image": "https://cdn.futbin.com/content/fifa25/img/players/231866.png"},
    {"name": "Lisandro Martinez", "nation": "🇦🇷 Argentina", "position": "ZAG", "club": "Manchester United", "rarity": "Comum", "overall": 66, "image": "https://cdn.futbin.com/content/fifa25/img/players/232730.png"},
    {"name": "Alejandro Garnacho", "nation": "🇦🇷 Argentina", "position": "PE", "club": "Manchester United", "rarity": "Comum", "overall": 65, "image": "https://cdn.futbin.com/content/fifa25/img/players/264657.png"},
    {"name": "Kobbie Mainoo", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Manchester United", "rarity": "Comum", "overall": 65, "image": "https://cdn.futbin.com/content/fifa25/img/players/256790.png"},
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

# ============ COG ============
class PackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_seconds = 30
    
    @app_commands.command(name="roll", description="🎲 Abre um pacote e revela um jogador da Copa 2026!")
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
                    f"⏳ Calma aí! Espera **{remaining}s** pra abrir outro pacote.",
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
        
        # Salvar no banco
        c.execute("""
            INSERT INTO user_players (user_id, player_name, player_nation, player_position, player_club, overall, rarity, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, player["name"], player["nation"], player["position"], 
              player["club"], player["overall"], player["rarity"], player["image"]))
        
        c.execute("""
            INSERT OR REPLACE INTO roll_cooldown (user_id, last_roll)
            VALUES (?, ?)
        """, (user_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Embed bonito com foto do jogador
        embed = discord.Embed(
            title=f"{config['emoji']} {player['rarity'].upper()}!",
            description=f"**{player['name']}** entrou pro seu time!",
            color=config["color"]
        )
        embed.add_field(name="🌍 Nação", value=player["nation"], inline=True)
        embed.add_field(name="⚽ Posição", value=player["position"], inline=True)
        embed.add_field(name="🏟️ Clube", value=player["club"], inline=True)
        embed.add_field(name="⭐ Overall", value=f"**{player['overall']}**", inline=True)
        embed.set_image(url=player["image"])  # Foto GRANDE do jogador
        embed.set_footer(text=f"Pack aberto por {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await msg.edit(embed=embed)
    
    @app_commands.command(name="probabilidades", description="📊 Ver as chances de cada raridade")
    async def probabilidades(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📊 Probabilidades dos Packs",
            description="Quanto mais raro, mais difícil de cair!",
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
