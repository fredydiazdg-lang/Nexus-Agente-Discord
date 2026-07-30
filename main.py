import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web  # 👈 Servidor web para Render

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Configuración de Intenciones Máximas
intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# 🚀 Función para responder a Render y evitar el error de puerto
async def handle(request):
    return web.Response(text="Nexus Bot está activo 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Servidor Web escuchando en el puerto {port} para Render.")

@bot.event
async def on_ready():
    print("==================================================")
    print(f"👑 NEXUS SUPREMO ACTIVO: {bot.user}")
    print(f"📍 Servidores vinculados: {len(bot.guilds)}")
    
    # 🚀 Sincronización instantánea por servidor
    try:
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"⚡ Sincronizados {len(synced)} comandos Slash instantáneamente en: {guild.name}")
    except Exception as e:
        print(f"❌ Error sincronizando comandos Slash: {e}")

    print("==================================================")
    await bot.change_presence(
        activity=discord.Streaming(
            name="🔥 El Servidor Supremo | !ayuda",
            url="https://www.twitch.tv/discord"
        )
    )

async def cargar_modulos():
    # Crea la carpeta 'cogs' automáticamente si no existe
    if not os.path.exists("./cogs"):
        os.makedirs("./cogs")
        print("📁 Carpeta 'cogs' creada con éxito.")

    for archivo in os.listdir("./cogs"):
        if archivo.endswith(".py"):
            await bot.load_extension(f"cogs.{archivo[:-3]}")
            print(f"✅ Módulo cargado correctamente: {archivo}")

async def main():
    async with bot:
        await start_web_server()  # 👈 Inicia el servidor web justo antes de encender el bot
        await cargar_modulos()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
