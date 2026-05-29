import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():
    print(f"\n🌍 Bot da Copa 2026 online!")
    print(f"⚽ Logado como: {bot.user.name}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"📊 Servidores: {len(bot.guilds)}")
    print("-" * 40)

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados!")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")

    # Status personalizado
    await bot.change_presence(
        activity=discord.Game(name="/roll | Copa do Mundo 2026 🏆"),
        status=discord.Status.online
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

async def load_extensions():
    await bot.load_extension("cogs.pack")
    await bot.load_extension("cogs.collection")
    await bot.load_extension("cogs.leaderboard")

async def main():
    async with bot:
        await load_extensions()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("❌ DISCORD_TOKEN não encontrado no .env!")
            return
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
