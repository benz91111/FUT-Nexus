import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from collections import Counter

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

class CollectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="📋 Ver sua coleção de jogadores da Copa 2026")
    async def status(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM user_players 
            WHERE user_id = ? 
            ORDER BY overall DESC, rolled_at DESC
        """, (user_id,))
        players = c.fetchall()
        conn.close()

        if not players:
            embed = discord.Embed(
                title="📭 Coleção Vazia",
                description="Você ainda não abriu nenhum pack! Use `/roll` pra começar.",
                color=0x95a5a6
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Estatísticas
        total = len(players)
        unique = len(set(p["player_name"] for p in players))
        rarities = Counter(p["rarity"] for p in players)
        best = max(players, key=lambda p: p["overall"])
        avg_ovr = sum(p["overall"] for p in players) // total

        embed = discord.Embed(
            title=f"🏆 Coleção de {interaction.user.display_name}",
            description=f"**{total}** jogadores encontrados | **{unique}** diferentes",
            color=0xFFD700
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        # Resumo de raridades
        rarity_text = ""
        for rarity in ["Ícone", "Lendário", "Épico", "Raro", "Comum"]:
            count = rarities.get(rarity, 0)
            emoji = RARITY_CONFIG[rarity]["emoji"]
            rarity_text += f"{emoji} **{rarity}**: {count}\n"

        embed.add_field(name="📊 Raridades", value=rarity_text, inline=True)
        embed.add_field(name="⭐ Melhor Jogador", value=f"**{best['player_name']}**\nOVR: {best['overall']} {RARITY_CONFIG[best['rarity']]['emoji']}", inline=True)
        embed.add_field(name="📈 Média OVR", value=f"**{avg_ovr}**", inline=True)

        # Top 5 jogadores
        top_players = players[:5]
        top_text = ""
        for i, p in enumerate(top_players, 1):
            emoji = RARITY_CONFIG[p["rarity"]]["emoji"]
            top_text += f"{i}. {emoji} **{p['player_name']}** ({p['overall']}) - {p['position']}\n"

        embed.add_field(name="🔝 Top 5", value=top_text, inline=False)
        embed.set_footer(text="Use /roll pra adicionar mais jogadores à sua coleção!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="jogadores", description="🔍 Ver todos os jogadores disponíveis no bot")
    async def jogadores(self, interaction: discord.Interaction):
        from cogs.pack import PLAYERS_BY_RARITY, RARITY_CONFIG

        embed = discord.Embed(
            title="🌍 Jogadores da Copa 2026",
            description="Todos os jogadores disponíveis nos packs!",
            color=0x2ecc71
        )

        for rarity in ["Ícone", "Lendário", "Épico", "Raro", "Comum"]:
            players = PLAYERS_BY_RARITY.get(rarity, [])
            if players:
                names = ", ".join([f"{p['name']} ({p['overall']})" for p in players[:8]])
                if len(players) > 8:
                    names += f" e mais {len(players) - 8}..."
                emoji = RARITY_CONFIG[rarity]["emoji"]
                embed.add_field(
                    name=f"{emoji} {rarity} ({len(players)})",
                    value=names,
                    inline=False
                )

        embed.set_footer(text="Boa sorte pra pegar os Ícones! 🍀")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="duplicatas", description="🔄 Ver jogadores repetidos na sua coleção")
    async def duplicatas(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT player_name, rarity, overall, COUNT(*) as count
            FROM user_players 
            WHERE user_id = ?
            GROUP BY player_name
            HAVING count > 1
            ORDER BY count DESC, overall DESC
        """, (user_id,))
        dups = c.fetchall()
        conn.close()

        if not dups:
            await interaction.response.send_message("🎉 Você não tem nenhuma duplicata! Todos únicos!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔄 Duplicatas",
            description=f"Você tem **{len(dups)}** jogadores repetidos:",
            color=0xe67e22
        )

        text = ""
        for d in dups:
            emoji = RARITY_CONFIG[d["rarity"]]["emoji"]
            text += f"{emoji} **{d['player_name']}** ({d['overall']}) - {d['count']}x\n"

        embed.add_field(name="Jogadores", value=text, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CollectionCog(bot))
