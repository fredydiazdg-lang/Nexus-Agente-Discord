import discord
from discord.ext import commands
import time

# Configuración: máximo 5 mensajes en un intervalo de 4 segundos
LIMITE_MENSAJES = 5
INTERVALO_SEGUNDOS = 4

class AntiFlood(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.historial_usuarios = {}  # {user_id: [timestamp1, timestamp2, ...]}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.guild_permissions.administrator:
            return

        user_id = message.author.id
        ahora = time.time()

        if user_id not in self.historial_usuarios:
            self.historial_usuarios[user_id] = []

        # Filtrar solo marcas de tiempo dentro del intervalo
        self.historial_usuarios[user_id] = [
            t for t in self.historial_usuarios[user_id] if ahora - t < INTERVALO_SEGUNDOS
        ]

        self.historial_usuarios[user_id].append(ahora)

        # Si supera el límite de mensajes permitidos
        if len(self.historial_usuarios[user_id]) >= LIMITE_MENSAJES:
            self.historial_usuarios[user_id] = []
            
            # Intentar borrar los mensajes spameados en el canal
            try:
                await message.channel.purge(limit=LIMITE_MENSAJES, check=lambda m: m.author == message.author)
            except Exception:
                pass

            aviso = await message.channel.send(
                f"⚠️ {message.author.mention}, estás enviando mensajes demasiado rápido (Anti-Flood)."
            )
            await aviso.delete(delay=5)

async def setup(bot):
    await bot.add_cog(AntiFlood(bot))