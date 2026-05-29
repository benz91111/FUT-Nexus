import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import os

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
    conn = sqlite3.connect("data/players.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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
PLAYERS = [
    # ÍCONES (OVR 92-99)
    {"name": "Lionel Messi", "nation": "🇦🇷 Argentina", "position": "ATA", "club": "Inter Miami", "rarity": "Ícone", "overall": 95, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p22102.png"},
    {"name": "Cristiano Ronaldo", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Al Nassr", "rarity": "Ícone", "overall": 93, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p14937.png"},
    {"name": "Neymar Jr", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Al Hilal", "rarity": "Ícone", "overall": 92, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p19054.png"},
    {"name": "Kylian Mbappé", "nation": "🇫🇷 França", "position": "ATA", "club": "Real Madrid", "rarity": "Ícone", "overall": 97, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p231747.png"},
    {"name": "Erling Haaland", "nation": "🇳🇴 Noruega", "position": "ATA", "club": "Manchester City", "rarity": "Ícone", "overall": 96, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p223094.png"},

    # LENDÁRIOS (OVR 87-91)
    {"name": "Vinicius Jr", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Lendário", "overall": 91, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p231804.png"},
    {"name": "Jude Bellingham", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Real Madrid", "rarity": "Lendário", "overall": 90, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244851.png"},
    {"name": "Rodri", "nation": "🇪🇸 Espanha", "position": "VOL", "club": "Manchester City", "rarity": "Lendário", "overall": 90, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p220566.png"},
    {"name": "Phil Foden", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Manchester City", "rarity": "Lendário", "overall": 89, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p209244.png"},
    {"name": "Bukayo Saka", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PD", "club": "Arsenal", "rarity": "Lendário", "overall": 89, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p223340.png"},
    {"name": "Jamal Musiala", "nation": "🇩🇪 Alemanha", "position": "ME", "club": "Bayern Munich", "rarity": "Lendário", "overall": 88, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p245669.png"},
    {"name": "Florian Wirtz", "nation": "🇩🇪 Alemanha", "position": "ME", "club": "Bayer Leverkusen", "rarity": "Lendário", "overall": 88, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p247819.png"},
    {"name": "Lamine Yamal", "nation": "🇪🇸 Espanha", "position": "PD", "club": "Barcelona", "rarity": "Lendário", "overall": 87, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p466850.png"},
    {"name": "Pedri", "nation": "🇪🇸 Espanha", "position": "MC", "club": "Barcelona", "rarity": "Lendário", "overall": 87, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244855.png"},
    {"name": "Endrick", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Real Madrid", "rarity": "Lendário", "overall": 87, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p466860.png"},

    # ÉPICOS (OVR 82-86)
    {"name": "Federico Valverde", "nation": "🇺🇾 Uruguai", "position": "MC", "club": "Real Madrid", "rarity": "Épico", "overall": 86, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p223255.png"},
    {"name": "Enzo Fernández", "nation": "🇦🇷 Argentina", "position": "MC", "club": "Chelsea", "rarity": "Épico", "overall": 86, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p448047.png"},
    {"name": "Alexis Mac Allister", "nation": "🇦🇷 Argentina", "position": "MC", "club": "Liverpool", "rarity": "Épico", "overall": 85, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p243050.png"},
    {"name": "Declan Rice", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "VOL", "club": "Arsenal", "rarity": "Épico", "overall": 85, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p204480.png"},
    {"name": "Bruno Guimarães", "nation": "🇧🇷 Brasil", "position": "MC", "club": "Newcastle", "rarity": "Épico", "overall": 85, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p224843.png"},
    {"name": "Rodrygo", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Real Madrid", "rarity": "Épico", "overall": 84, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p231804.png"},
    {"name": "Gavi", "nation": "🇪🇸 Espanha", "position": "MC", "club": "Barcelona", "rarity": "Épico", "overall": 84, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p456607.png"},
    {"name": "Khvicha Kvaratskhelia", "nation": "🇬🇪 Geórgia", "position": "PE", "club": "PSG", "rarity": "Épico", "overall": 83, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p446531.png"},
    {"name": "William Saliba", "nation": "🇫🇷 França", "position": "ZAG", "club": "Arsenal", "rarity": "Épico", "overall": 83, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p462424.png"},
    {"name": "Rafael Leão", "nation": "🇵🇹 Portugal", "position": "PE", "club": "AC Milan", "rarity": "Épico", "overall": 82, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p216073.png"},
    {"name": "Victor Osimhen", "nation": "🇳🇬 Nigéria", "position": "ATA", "club": "Galatasaray", "rarity": "Épico", "overall": 82, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p216073.png"},
    {"name": "Kai Havertz", "nation": "🇩🇪 Alemanha", "position": "ATA", "club": "Arsenal", "rarity": "Épico", "overall": 82, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p192895.png"},

    # RAROS (OVR 75-81)
    {"name": "Julian Alvarez", "nation": "🇦🇷 Argentina", "position": "ATA", "club": "Atletico Madrid", "rarity": "Raro", "overall": 81, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p218667.png"},
    {"name": "Nicolas Jackson", "nation": "🇸🇳 Senegal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 80, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244850.png"},
    {"name": "Cole Palmer", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Chelsea", "rarity": "Raro", "overall": 80, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244851.png"},
    {"name": "Gabriel Martinelli", "nation": "🇧🇷 Brasil", "position": "PE", "club": "Arsenal", "rarity": "Raro", "overall": 79, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p444145.png"},
    {"name": "Martin Ødegaard", "nation": "🇳🇴 Noruega", "position": "ME", "club": "Arsenal", "rarity": "Raro", "overall": 79, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p184029.png"},
    {"name": "Diogo Jota", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p194634.png"},
    {"name": "Darwin Núñez", "nation": "🇺🇾 Uruguai", "position": "ATA", "club": "Liverpool", "rarity": "Raro", "overall": 78, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p447117.png"},
    {"name": "Christopher Nkunku", "nation": "🇫🇷 França", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 77, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p230142.png"},
    {"name": "Dominik Szoboszlai", "nation": "🇭🇺 Hungria", "position": "MC", "club": "Liverpool", "rarity": "Raro", "overall": 77, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p424876.png"},
    {"name": "João Félix", "nation": "🇵🇹 Portugal", "position": "ATA", "club": "Chelsea", "rarity": "Raro", "overall": 76, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p230142.png"},
    {"name": "Georginio Rutter", "nation": "🇫🇷 França", "position": "ATA", "club": "Brighton", "rarity": "Raro", "overall": 76, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p446531.png"},
    {"name": "Micky van de Ven", "nation": "🇳🇱 Holanda", "position": "ZAG", "club": "Tottenham", "rarity": "Raro", "overall": 75, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p443988.png"},
    {"name": "Jeremy Doku", "nation": "🇧🇪 Bélgica", "position": "PE", "club": "Manchester City", "rarity": "Raro", "overall": 75, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244851.png"},
    {"name": "Benjamin Sesko", "nation": "🇸🇮 Eslovênia", "position": "ATA", "club": "RB Leipzig", "rarity": "Raro", "overall": 75, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p466850.png"},

    # COMUNS (OVR 65-74)
    {"name": "Conor Gallagher", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Atletico Madrid", "rarity": "Comum", "overall": 74, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p232787.png"},
    {"name": "Morgan Rogers", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Aston Villa", "rarity": "Comum", "overall": 73, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244850.png"},
    {"name": "Dejan Kulusevski", "nation": "🇸🇪 Suécia", "position": "PD", "club": "Tottenham", "rarity": "Comum", "overall": 73, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p221239.png"},
    {"name": "Brennan Johnson", "nation": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 72, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p445044.png"},
    {"name": "Morgan Gibbs-White", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Nottingham Forest", "rarity": "Comum", "overall": 72, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p222531.png"},
    {"name": "Anthony Gordon", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PE", "club": "Newcastle", "rarity": "Comum", "overall": 71, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p243050.png"},
    {"name": "Curtis Jones", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Liverpool", "rarity": "Comum", "overall": 71, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p206915.png"},
    {"name": "Eberechi Eze", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Crystal Palace", "rarity": "Comum", "overall": 70, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p232413.png"},
    {"name": "Dominic Solanke", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ATA", "club": "Tottenham", "rarity": "Comum", "overall": 70, "image": "https://resources.premierleague.com/premierleague.com/photos/players/250x250/p173514.png"},
    {"name": "Jarrod Bowen", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "PD", "club": "West Ham", "rarity": "Comum", "overall": 69, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p178186.png"},
    {"name": "James Ward-Prowse", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "West Ham", "rarity": "Comum", "overall": 69, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p156689.png"},
    {"name": "Pedro Neto", "nation": "🇵🇹 Portugal", "position": "PE", "club": "Chelsea", "rarity": "Comum", "overall": 68, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p220566.png"},
    {"name": "João Pedro", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Brighton", "rarity": "Comum", "overall": 68, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244850.png"},
    {"name": "Matheus Cunha", "nation": "🇧🇷 Brasil", "position": "ATA", "club": "Wolves", "rarity": "Comum", "overall": 67, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p430160.png"},
    {"name": "Morgan Rogers", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "ME", "club": "Aston Villa", "rarity": "Comum", "overall": 67, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p244850.png"},
    {"name": "Trent Alexander-Arnold", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "LD", "club": "Liverpool", "rarity": "Comum", "overall": 66, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p169187.png"},
    {"name": "Lisandro Martinez", "nation": "🇦🇷 Argentina", "position": "ZAG", "club": "Manchester United", "rarity": "Comum", "overall": 66, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p221239.png"},
    {"name": "Alejandro Garnacho", "nation": "🇦🇷 Argentina", "position": "PE", "club": "Manchester United", "rarity": "Comum", "overall": 65, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p488404.png"},
    {"name": "Kobbie Mainoo", "nation": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "position": "MC", "club": "Manchester United", "rarity": "Comum", "overall": 65, "image": "https://resources.premierleague.com/premierleague/photos/players/250x250/p477558.png"},
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
    """Gera uma cartinha estilo FIFA com a foto do jogador"""

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

    # Área da foto (topo)
    photo_area = (30, 30, 370, 320)

    # Tentar baixar foto do jogador
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(player["image"], timeout=5) as resp:
                if resp.status == 200:
                    photo_data = await resp.read()
                    photo = Image.open(io.BytesIO(photo_data)).convert("RGBA")
                    photo = photo.resize((340, 290), Image.LANCZOS)

                    # Criar máscara circular
                    mask = Image.new("L", (340, 290), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([0, 0, 340, 290], fill=255)

                    img.paste(photo, (30, 30), mask)
    except Exception:
        # Fallback: desenhar silhueta
        draw.ellipse([30, 30, 370, 320], fill=(50, 50, 50, 200), outline=(255, 255, 255, 100), width=3)
        draw.text((200, 175), "📷", fill=(255, 255, 255, 200), anchor="mm")

    # Overall badge
    badge_color = config["color"]
    draw.ellipse([20, 340, 100, 420], fill=badge_color, outline=(255, 255, 255, 255), width=3)

    # Fontes (usar fonte padrão se não encontrar)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
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
    draw.text((200, 485), player["nation"], fill=(255, 255, 255, 200), font=font_small, anchor="mm")

    # Clube
    draw.text((200, 515), player["club"], fill=(255, 255, 255, 180), font=font_tiny, anchor="mm")

    # Raridade badge
    rarity_text = f"{config['emoji']} {player['rarity'].upper()}"

    # Fundo da raridade
    text_bbox = draw.textbbox((0, 0), rarity_text, font=font_small)
    text_width = text_bbox[2] - text_bbox[0]
    badge_x = (width - text_width) // 2 - 10
    draw.rounded_rectangle(
        [badge_x, 545, badge_x + text_width + 20, 575],
        radius=10,
        fill=(0, 0, 0, 180),
        outline=(255, 255, 255, 100),
        width=2
    )
    draw.text((width//2, 560), rarity_text, fill=(255, 255, 255, 255), font=font_small, anchor="mm")

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
        self.cooldown_seconds = 30  # Cooldown entre rolls

    @app_commands.command(name="roll", description="🎲 Abre um pacote e revela um jogador da Copa 2026!")
    async def roll(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Verificar cooldown
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

        # Animação de abertura
        embed = discord.Embed(
            title="🎁 ABRINDO PACOTE...",
            description="Preparando seu pack da Copa 2026...",
            color=0xFFD700
        )
        msg = await interaction.followup.send(embed=embed)

        await asyncio.sleep(1.5)

        # Roll do jogador
        player = roll_player()
        config = RARITY_CONFIG[player["rarity"]]

        # Gerar cartinha
        try:
            card_buffer = await generate_card(player)
            card_file = discord.File(card_buffer, filename="card.png")
        except Exception as e:
            card_file = None
            print(f"Erro ao gerar carta: {e}")

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

        # Embed final
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
