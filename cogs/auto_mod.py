import re
import discord
from discord.ext import commands

INSULTOS_PROHIBIDOS = ["palabrota1", "palabrota2"] # Agrega aquí palabras que no quieras en tu server

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.guild_permissions.administrator:
            return

        contenido = message.content

        # A) Filtro de Mayúsculas Masivas (Gritos/Spam)
        if len(contenido) > 10 and sum(1 for c in contenido if c.isupper()) / len(contenido) > 0.7:
            await message.delete()
            warning = await message.channel.send(f"⚠️ {message.author.mention}, no abuses de las MAYÚSCULAS.")
            await warning.delete(delay=5)
            return

        # B) Filtro de Menciones Masivas Anti-Raid
        if len(message.mentions) > 4:
            await message.delete()
            warning = await message.channel.send(f"🚨 {message.author.mention} intentó hacer spam de menciones.")
            await warning.delete(delay=5)
            return

        # C) Filtro de Insultos
        if any(palabra in contenido.lower() for palabra in INSULTOS_PROHIBIDOS):
            await message.delete()
            warning = await message.channel.send(f"🤬 {message.author.mention}, mantén un lenguaje respetuoso.")
            await warning.delete(delay=5)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))