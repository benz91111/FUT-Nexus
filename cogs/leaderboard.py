import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

def get_db():
    conn = sqlite3.connect("data/players.db")
    conn.row_factory = sqlite3.Row
    return conn

RARITY_CONFIG = {
    "Comum": {"color": 0x95a5a6, "emoji": "⚪"},
    "Raro": {"color": 0x3498db, "emoji": "🔵"},
    "Épico": {"color": 0x9b59b6, "emoji": "🟣"},
    "Lendário": {"color": 0xf1c40f, "emoji": "🟡"},
    "Ícone": {"color": 0xe74c3c, "emoji": "🔴"}
}

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ranking", description="🏆 Ver o ranking global de colecionadores")
    async def ranking(self, interaction: discord.Interaction):
        conn = get_db()
        c = conn.cursor()

        # Ranking por quantidade de jogadores
        c.execute("""
            SELECT user_id, COUNT(*) as total, MAX(overall) as best_ovr
            FROM user_players
            GROUP BY user_id
            ORDER BY total DESC, best_ovr DESC
            LIMIT 10
        """)
        top_collectors = c.fetchall()

        # Ranking por melhor jogador
        c.execute("""
            SELECT user_id, player_name, overall, rarity
            FROM user_players
            WHERE overall = (SELECT MAX(overall) FROM user_players AS sub WHERE sub.user_id = user_players.user_id)
            GROUP BY user_id
            ORDER BY overall DESC
            LIMIT 5
        """)
        top_players = c.fetchall()

        conn.close()

        embed = discord.Embed(
            title="🏆 Ranking Global - Copa 2026",
            description="Os maiores colecionadores do servidor!",
            color=0xFFD700
        )

        # Top colecionadores
        if top_collectors:
            text = ""
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for i, row in enumerate(top_collectors):
                user = self.bot.get_user(int(row["user_id"]))
                name = user.display_name if user else f"Usuário {row['user_id'][:6]}..."
                medal = medals[i] if i < len(medals) else "🔹"
                text += f"{medal} **{name}** - {row['total']} jogadores (Melhor: {row['best_ovr']} OVR)\n"
            embed.add_field(name="📊 Mais Jogadores", value=text, inline=False)

        # Top jogadores
        if top_players:
            text = ""
            for row in top_players:
                user = self.bot.get_user(int(row["user_id"]))
                name = user.display_name if user else f"Usuário {row['user_id'][:6]}..."
                emoji = RARITY_CONFIG[row["rarity"]]["emoji"]
                text += f"{emoji} **{row['player_name']}** ({row['overall']}) - {name}\n"
            embed.add_field(name="⭐ Melhores Jogadores", value=text, inline=False)

        embed.set_footer(text="Abra packs com /roll pra subir no ranking!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="perfil", description="👤 Ver perfil detalhado de um usuário")
    @app_commands.describe(user="Usuário pra ver o perfil (deixe em branco pra ver o seu)")
    async def perfil(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        user_id = str(target.id)

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM user_players 
            WHERE user_id = ? 
            ORDER BY overall DESC
        """, (user_id,))
        players = c.fetchall()
        conn.close()

        if not players:
            await interaction.response.send_message(
                f"📭 {target.display_name} ainda não tem nenhum jogador!",
                ephemeral=True
            )
            return

        total = len(players)
        unique = len(set(p["player_name"] for p in players))
        best = max(players, key=lambda p: p["overall"])
        avg_ovr = sum(p["overall"] for p in players) // total

        # Contar raridades
        rarities = {"Comum": 0, "Raro": 0, "Épico": 0, "Lendário": 0, "Ícone": 0}
        for p in players:
            if p["rarity"] in rarities:
                rarities[p["rarity"]] += 1

        embed = discord.Embed(
            title=f"👤 Perfil de {target.display_name}",
            description=f"Colecionador da Copa 2026 🏆",
            color=RARITY_CONFIG[best["rarity"]]["color"]
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(name="📊 Total", value=f"**{total}** jogadores", inline=True)
        embed.add_field(name="🎯 Únicos", value=f"**{unique}** diferentes", inline=True)
        embed.add_field(name="⭐ Média OVR", value=f"**{avg_ovr}**", inline=True)

        rarity_text = ""
        for r, count in rarities.items():
            if count > 0:
                emoji = RARITY_CONFIG[r]["emoji"]
                rarity_text += f"{emoji} {r}: {count}\n"

        embed.add_field(name="🎲 Raridades", value=rarity_text or "Nenhuma", inline=True)
        embed.add_field(name="🔝 Melhor Jogador", value=f"**{best['player_name']}**\n{best['overall']} OVR {RARITY_CONFIG[best['rarity']]['emoji']}", inline=True)
        embed.add_field(name="🏟️ Clube", value=best["club"], inline=True)

        embed.set_footer(text=f"ID: {target.id}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
