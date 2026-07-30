import discord
from discord.ext import commands
import re

# Palabras clave y dominios sospechosos comunes de estafas
PATRONES_SCAM = [
    r"free-nitro", r"nitro-free", r"discord-gift", r"discorcl", r"dlscord",
    r"diamantes-gratis", r"free-diamonds", r"freefire-gems", r"steam-gift",
    r"generador-diamantes", r"recarga-gratis", r"claim-nitro", r"gift-nitro"
]

class AntiScamInteligente(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Omitir administradores
        if message.author.guild_permissions.administrator:
            return

        contenido = message.content.lower()

        # Buscar si el mensaje contiene alguna combinación de estafa
        es_scam = any(re.search(patron, contenido) for patron in PATRONES_SCAM)

        if es_scam:
            try:
                await message.delete()
            except Exception:
                pass

            # Avisar al usuario en el chat
            aviso = await message.channel.send(
                f"🚨 {message.author.mention}, tu mensaje fue eliminado por sospecha de **enlace malicioso o estafa (Anti-Scam Security)**."
            )
            
            # Registrar en el canal de logs si existe
            canal_logs = discord.utils.get(message.guild.text_channels, name="logs") or discord.utils.get(message.guild.text_channels, name="auditoria")
            if canal_logs:
                embed = discord.Embed(
                    title="🛡️ Enlace Malicioso Bloqueado (Anti-Scam)",
                    description=f"**Usuario:** {message.author.mention} (`{message.author.id}`)\n**Canal:** {message.channel.mention}\n**Contenido bloqueado:**\n```{message.content}```",
                    color=discord.Color.dark_red()
                )
                await canal_logs.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiScamInteligente(bot))