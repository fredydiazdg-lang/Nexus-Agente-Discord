import re
import discord
from discord.ext import commands

# Excepciones de enlaces permitidos (ej. tu propio TikTok, YouTube o enlaces de Discord)
DOMINIOS_PERMITIDOS = ["tiktok.com", "youtube.com", "youtu.be", "discord.gg"]

class AntiLinks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.guild_permissions.administrator:
            return

        # Expresión regular para detectar enlaces de internet (http / https)
        patron_url = r"https?://[^\s]+"
        urls = re.findall(patron_url, message.content.lower())

        if urls:
            # Revisar si el enlace pertenece a la lista blanca
            permitido = any(any(dom in url for dom in DOMINIOS_PERMITIDOS) for url in urls)

            if not permitido:
                await message.delete()
                aviso = await message.channel.send(
                    f"🚫 {message.author.mention}, no está permitido enviar enlaces externos o spam de otros servidores."
                )
                await aviso.delete(delay=5)

async def setup(bot):
    await bot.add_cog(AntiLinks(bot))