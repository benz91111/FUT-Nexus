import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sqlite3
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp

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

# ============ JOGADORES DA COPA 2026 - FOTOS REAIS ============
PLAYERS = [
    # ÍCONES (OVR 92-99)
    {"name": "Lionel Messi", "nation": "🇦🇷 Argentina", "position": "ATA", "club": "Inter Miami", "rarity": "Ícone", "overall": 95, "image": "https://img.a.transfermarkt.technology/portrait/header/28003-1716899475.jpg"},
    {"name": "Cristiano Ronaldo", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Al Nassr", "rarity": "Ícone", "overall": 93, "image": "https://img.a.transfermarkt.technology/portrait/header/8198-1694609670.jpg"},
    {"name": "Neymar Jr", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Al Hilal", "rarity": "Ícone", "overall": 92, "image": "https://img.a.transfermarkt.technology/portrait/header/68290-1697050462.jpg"},
    {"name": "Kylian Mbappé", "nation": "🇫🇷 França", "position": "ATA", "club": "Real Madrid", "rarity": "Ícone", "overall": 97, "image": "https://img.a.transfermarkt.technology/portrait/header/342229-1718095136.jpg"},
    {"name": "Erling Haaland", "nation": "🇳🇴 Noruega", "position": "ATA", "club": "Manchester City", "rarity": "Ícone", "overall": 96, "image": "https://img.a.transfermarkt.technology/portrait/header/418560-1708933853.jpg"},
    
    # LENDÁRIOS (OVR 87-91)
    {"name": "Vinicius Jr", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Lendário", "overall": 91, "image": "https://img.a.transfermarkt.technology/portrait/header/371998-1664869583.jpg"},
    {"name": "Jude Bellingham", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Real Madrid", "rarity": "Lendário", "overall": 90, "image": "https://img.a.transfermarkt.technology/portrait/header/581678-1700653146.jpg"},
    {"name": "Rodri", "nation": "🇪🇸 Espanha", "position": "VOL", "club": "Manchester City", "rarity": "Lendário", "overall": 90, "image": "https://img.a.transfermarkt.technology/portrait/header/357565-1700653601.jpg"},
    {"name": "Phil Foden", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Manchester City", "rarity": "Lendário", "overall": 89, "image": "https://img.a.transfermarkt.technology/portrait/header/406635-1700652988.jpg"},
    {"name": "Bukayo Saka", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PD", "club": "Arsenal", "rarity": "Lendário", "overall": 89, "image": "https://img.a.transfermarkt.technology/portrait/header/433177-1668517789.jpg"},
    {"name": "Jamal Musiala", "nation": "🇩🇪 Alemanha", "position": "ME", "club": "Bayern Munich", "rarity": "Lendário", "overall": 88, "image": "https://img.a.transfermarkt.technology/portrait/header/580195-1700652856.jpg"},
    {"name": "Florian Wirtz", "nation": "🇩🇪 Alemanha", "position": "ME", "club": "Bayer Leverkusen", "rarity": "Lendário", "overall": 88, "image": "https://img.a.transfermarkt.technology/portrait/header/598577-1700652773.jpg"},
    {"name": "Lamine Yamal", "nation": "🇪🇸 Espanha", "position": "PD", "club": "Barcelona", "rarity": "Lendário", "overall": 87, "image": "https://img.a.transfermarkt.technology/portrait/header/937958-1712577426.jpg"},
    {"name": "Pedri", "nation": "🇪🇸 Espanha", "position": "MC", "club": "Barcelona", "rarity": "Lendário", "overall": 87, "image": "https://img.a.transfermarkt.technology/portrait/header/683840-1667830804.jpg"},
    {"name": "Endrick", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Real Madrid", "rarity": "Lendário", "overall": 87, "image": "https://img.a.transfermarkt.technology/portrait/header/987128-1704295569.jpg"},
    
    # ÉPICOS (OVR 82-86)
    {"name": "Federico Valverde", "nation": "🇺🇾 Uruguai", "position": "MC", "club": "Real Madrid", "rarity": "Épico", "overall": 86, "image": "https://img.a.transfermarkt.technology/portrait/header/369081-1700653469.jpg"},
    {"name": "Enzo Fernández", "nation": "🇦🇷 Argentina", "position": "MC", "club": "Chelsea", "rarity": "Épico", "overall": 86, "image": "https://img.a.transfermarkt.technology/portrait/header/648195-1700653334.jpg"},
    {"name": "Alexis Mac Allister", "nation": "🇦🇷 Argentina", "position": "MC", "club": "Liverpool", "rarity": "Épico", "overall": 85, "image": "https://img.a.transfermarkt.technology/portrait/header/534033-1700653387.jpg"},
    {"name": "Declan Rice", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "VOL", "club": "Arsenal", "rarity": "Épico", "overall": 85, "image": "https://img.a.transfermarkt.technology/portrait/header/357662-1700653120.jpg"},
    {"name": "Bruno Guimarães", "nation": "🇧🇷 Brasil", "position": "MC", "club": "Newcastle", "rarity": "Épico", "overall": 85, "image": "https://img.a.transfermarkt.technology/portrait/header/520624-1700653266.jpg"},
    {"name": "Rodrygo", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Épico", "overall": 84, "image": "https://img.a.transfermarkt.technology/portrait/header/412363-1700653511.jpg"},
    {"name": "Gavi", "nation": "🇪🇸 Espanha", "position": "MC", "club": "Barcelona", "rarity": "Épico", "overall": 84, "image": "https://img.a.transfermarkt.technology/portrait/header/646740-1667830714.jpg"},
    {"name": "Khvicha Kvaratskhelia", "nation": "🇬🇪 Geórgia", "position": "PE", "club": "PSG", "rarity": "Épico", "overall": 83, "image": "https://img.a.transfermarkt.technology/portrait/header/502670-1700652935.jpg"},
    {"name": "William Saliba", "nation": "🇫🇷 França", "position": "ZAG", "club": "Arsenal", "rarity": "Épico", "overall": 83, "image": "https://img.a.transfermarkt.technology/portrait/header/495666-1700653093.jpg"},
    {"name": "Rafael Leão", "nation": "🇵🇹 Portugal", "position": "PE", "club": "AC Milan", "rarity": "Épico", "overall": 82, "image": "https://img.a.transfermarkt.technology/portrait/header/357164-1700653204.jpg"},
    {"name": "Victor Osimhen", "nation": "🇳🇬 Nigéria", "position": "ATA", "club": "Galatasaray", "rarity": "Épico", "overall": 82, "image": "https://img.a.transfermarkt.technology/portrait/header/401923-1700653160.jpg"},
    {"name": "Kai Havertz", "nation": "🇩🇪 Alemanha", "position": "ATA", "club": "Arsenal", "rarity": "Épico", "overall": 82, "image": "https://img.a.transfermarkt.technology/portrait/header/309400-1700652840.jpg"},
    
    # RAROS (OVR 75-81)
    {"name": "Julian Alvarez", "nation": "🇦🇷 Argentina", "position": "ATA", "club": "Atletico Madrid", "rarity": "Raro", "overall": 81, "image": "https://img.a.transfermarkt.technology/portrait/header/576024-1700653352.jpg"},
    {"name": "Nicolas Jackson", "nation": "🇸🇳 Senegal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 80, "image": "https://img.a.transfermarkt.technology/portrait/header/503275-1700653321.jpg"},
    {"name": "Cole Palmer", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Chelsea", "rarity": "Raro", "overall": 80, "image": "https://img.a.transfermarkt.technology/portrait/header/559371-1700652964.jpg"},
    {"name": "Gabriel Martinelli", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Arsenal", "rarity": "Raro", "overall": 79, "image": "https://img.a.transfermarkt.technology/portrait/header/653052-1700653077.jpg"},
    {"name": "Martin Ødegaard", "nation": "🇳🇴 Noruega", "position": "ME", "club": "Arsenal", "rarity": "Raro", "overall": 79, "image": "https://img.a.transfermarkt.technology/portrait/header/316264-1700653106.jpg"},
    {"name": "Diogo Jota", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "image": "https://img.a.transfermarkt.technology/portrait/header/340950-1700653191.jpg"},
    {"name": "Darwin Núñez", "nation": "🇺🇾 Uruguai", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "image": "https://img.a.transfermarkt.technology/portrait/header/546543-1700653370.jpg"},
    {"name": "Christopher Nkunku", "nation": "🇫🇷 França", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 77, "image": "https://img.a.transfermarkt.technology/portrait/header/344381-1700653153.jpg"},
    {"name": "Dominik Szoboszlai", "nation": "🇭🇺 Hungria", "position": "MC", "club": "Liverpool", "rarity": "Raro", "overall": 77, "image": "https://img.a.transfermarkt.technology/portrait/header/451276-1700653394.jpg"},
    {"name": "João Félix", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 76, "image": "https://img.a.transfermarkt.technology/portrait/header/462250-1700653211.jpg"},
    {"name": "Georginio Rutter", "nation": "🇫🇷 França", "position": "ATA", "club": "Brighton", "rarity": "Raro", "overall": 76, "image": "https://img.a.transfermarkt.technology/portrait/header/567441-1700652942.jpg"},
    {"name": "Micky van de Ven", "nation": "🇳🇱 Holanda", "position": "ZAG", "club": "Tottenham", "rarity": "Raro", "overall": 75, "image": "https://img.a.transfermarkt.technology/portrait/header/597158-1700653540.jpg"},
    {"name": "Jeremy Doku", "nation": "🇧🇪 Bélgica", "position": "PE", "club": "Manchester City", "rarity": "Raro", "overall": 75, "image": "https://img.a.transfermarkt.technology/portrait/header/486049-1700652995.jpg"},
    {"name": "Benjamin Sesko", "nation": "🇸🇮 Eslovênia", "position": "ATA", "club": "RB Leipzig", "rarity": "Raro", "overall": 75, "image": "https://img.a.transfermarkt.technology/portrait/header/627495-1700652826.jpg"},
    
    # COMUNS (OVR 65-74)
    {"name": "Conor Gallagher", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Atletico Madrid", "rarity": "Comum", "overall": 74, "image": "https://img.a.transfermarkt.technology/portrait/header/488404-1700653314.jpg"},
    {"name": "Morgan Rogers", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Aston Villa", "rarity": "Comum", "overall": 73, "image": "https://img.a.transfermarkt.technology/portrait/header/477558-1700653056.jpg"},
    {"name": "Dejan Kulusevski", "nation": "🇸🇪 Suécia", "position": "PD", "club": "Tottenham", "rarity": "Comum", "overall": 73, "image": "https://img.a.transfermarkt.technology/portrait/header/413235-1700653533.jpg"},
    {"name": "Brennan Johnson", "nation": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 72, "image": "https://img.a.transfermarkt.technology/portrait/header/503276-1700653526.jpg"},
    {"name": "Morgan Gibbs-White", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Nottingham Forest", "rarity": "Comum", "overall": 72, "image": "https://img.a.transfermarkt.technology/portrait/header/434324-1700653049.jpg"},
    {"name": "Anthony Gordon", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PE", "club": "Newcastle", "rarity": "Comum", "overall": 71, "image": "https://img.a.transfermarkt.technology/portrait/header/503275-1700653273.jpg"},
    {"name": "Curtis Jones", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Liverpool", "rarity": "Comum", "overall": 71, "image": "https://img.a.transfermarkt.technology/portrait/header/405265-1700653363.jpg"},
    {"name": "Eberechi Eze", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Crystal Palace", "rarity": "Comum", "overall": 70, "image": "https://img.a.transfermarkt.technology/portrait/header/424876-1700653002.jpg"},
    {"name": "Dominic Solanke", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 70, "image": "https://img.a.transfermarkt.technology/portrait/header/346472-1700653063.jpg"},
    {"name": "Jarrod Bowen", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PD", "club": "West Ham", "rarity": "Comum", "overall": 69, "image": "https://img.a.transfermarkt.technology/portrait/header/326763-1700653554.jpg"},
    {"name": "James Ward-Prowse", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "West Ham", "rarity": "Comum", "overall": 69, "image": "https://img.a.transfermarkt.technology/portrait/header/156689-1700653561.jpg"},
    {"name": "Pedro Neto", "nation": "🇵🇹 Portugal", "position": "PE", "club": "Chelsea", "rarity": "Comum", "overall": 68, "image": "https://img.a.transfermarkt.technology/portrait/header/495666-1700653328.jpg"},
    {"name": "João Pedro", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Brighton", "rarity": "Comum", "overall": 68, "image": "https://img.a.transfermarkt.technology/portrait/header/645277-1700652949.jpg"},
    {"name": "Matheus Cunha", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Wolves", "rarity": "Comum", "overall": 67, "image": "https://img.a.transfermarkt.technology/portrait/header/534033-1700653401.jpg"},
    {"name": "Trent Alexander-Arnold", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "LD", "club": "Liverpool", "rarity": "Comum", "overall": 66, "image": "https://img.a.transfermarkt.technology/portrait/header/314353-1700653380.jpg"},
    {"name": "Lisandro Martinez", "nation": "🇦🇷 Argentina", "position": "ZAG", "club": "Manchester United", "rarity": "Comum", "overall": 66, "image": "https://img.a.transfermarkt.technology/portrait/header/482488-1700653345.jpg"},
    {"name": "Alejandro Garnacho", "nation": "🇦🇷 Argentina", "position": "PE", "club": "Manchester United", "rarity": "Comum", "overall": 65, "image": "https://img.a.transfermarkt.technology/portrait/header/668049-1667830772.jpg"},
    {"name": "Kobbie Mainoo", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Manchester United", "rarity": "Comum", "overall": 65, "image": "https://img.a.transfermarkt.technology/portrait/header/686578-1700653035.jpg"},
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

# ============ GERAR CARTINHA ============
async def generate_card(player):
    """Gera uma cartinha estilo FIFA com a foto real do jogador"""
    
    config = RARITY_CONFIG[player["rarity"]]
    
    # Criar imagem base
    width, height = 400, 600
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Cor de fundo baseada na raridade
    color = config["color"]
    r, g, b = (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF
    
    # Gradiente de fundo
    for y in range(height):
        alpha = int(255 * (1 - y / height * 0.3))
        draw.line([(0, y), (width, y)], fill=(r, g, b, alpha))
    
    # Borda dourada/brilhante
    border_width = 8
    draw.rectangle(
        [border_width//2, border_width//2, width-border_width//2, height-border_width//2],
        outline=(255, 215, 0, 255) if player["rarity"] == "Ícone" else (255, 255, 255, 200),
        width=border_width
    )
    
    # Tentar baixar foto do jogador
    photo_loaded = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(player["image"], timeout=8, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    photo_data = await resp.read()
                    photo = Image.open(io.BytesIO(photo_data)).convert("RGBA")
                    photo = photo.resize((340, 290), Image.LANCZOS)
                    
                    # Criar máscara circular
                    mask = Image.new("L", (340, 290), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([0, 0, 340, 290], fill=255)
                    
                    img.paste(photo, (30, 30), mask)
                    photo_loaded = True
    except Exception as e:
        print(f"Erro ao carregar foto de {player['name']}: {e}")
    
    if not photo_loaded:
        # Fallback: desenhar silhueta
        draw.ellipse([30, 30, 370, 320], fill=(50, 50, 50, 200), outline=(255, 255, 255, 100), width=3)
        draw.text((200, 175), "📷", fill=(255, 255, 255, 200), anchor="mm")
    
    # Overall badge
    badge_color = config["color"]
    draw.ellipse([20, 340, 100, 420], fill=badge_color, outline=(255, 255, 255, 255), width=3)
    
    # Fontes
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
        font_tiny = font_large
    
    # Overall number
    draw.text((60, 380), str(player["overall"]), fill=(255, 255, 255, 255), font=font_large, anchor="mm")
    
    # Posição
    draw.text((60, 410), player["position"], fill=(255, 255, 255, 200), font=font_tiny, anchor="mm")
    
    # Nome do jogador
    name = player["name"]
    if len(name) > 18:
        name = name[:17] + "..."
    draw.text((200, 450), name, fill=(255, 255, 255, 255), font=font_medium, anchor="mm")
    
    # Nação
    draw.text((200, 480), player["nation"], fill=(255, 255, 255, 200), font=font_small, anchor="mm")
    
    # Clube
    draw.text((200, 505), player["club"], fill=(255, 255, 255, 180), font=font_tiny, anchor="mm")
    
    # Raridade badge
    rarity_text = f"{config['emoji']} {player['rarity'].upper()}"
    
    # Fundo da raridade
    text_bbox = draw.textbbox((0, 0), rarity_text, font=font_small)
    text_width = text_bbox[2] - text_bbox[0]
    badge_x = (width - text_width) // 2 - 10
    draw.rounded_rectangle(
        [badge_x, 540, badge_x + text_width + 20, 570],
        radius=10,
        fill=(0, 0, 0, 180),
        outline=(255, 255, 255, 100),
        width=2
    )
    draw.text((width//2, 555), rarity_text, fill=(255, 255, 255, 255), font=font_small, anchor="mm")
    
    # Salvar em buffer
    buffer = io.BytesIO()
    img = img.convert("RGB")
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return buffer

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
        
        try:
            card_buffer = await generate_card(player)
            card_file = discord.File(card_buffer, filename="card.png")
        except Exception as e:
            card_file = None
            print(f"Erro ao gerar carta: {e}")
        
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
        
        embed = discord.Embed(
            title=f"{config['emoji']} {player['rarity'].upper()}!",
            description=f"**{player['name']}** entrou pro seu time!",
            color=config["color"]
        )
        embed.add_field(name="🌍 Nação", value=player["nation"], inline=True)
        embed.add_field(name="⚽ Posição", value=player["position"], inline=True)
        embed.add_field(name="🏟️ Clube", value=player["club"], inline=True)
        embed.add_field(name="⭐ Overall", value=f"**{player['overall']}**", inline=True)
        embed.set_footer(text=f"Pack aberto por {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        if card_file:
            embed.set_image(url="attachment://card.png")
            await msg.edit(embed=embed, attachments=[card_file])
        else:
            embed.set_thumbnail(url=player["image"])
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
