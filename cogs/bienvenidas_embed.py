import discord
from discord.ext import commands

# 📌 PEGA AQUÍ EL ID DE TU CANAL DE BIENVENIDA (#bienvenida / #llegadas)
ID_CANAL_BIENVENIDA = 1405271614404296827  # Reemplaza con el ID de tu canal

class BienvenidasEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        canal = self.bot.get_channel(ID_CANAL_BIENVENIDA)
        if not canal:
            return

        total_miembros = len(member.guild.members)

        embed = discord.Embed(
            title=f"👋 ¡BIENVENIDO/A A {member.guild.name.upper()}!",
            description=(
                f"¡Hola {member.mention}! Nos alegra mucho tenerte en la comunidad.\n\n"
                f"📜 No olvides leer las **reglas** del servidor.\n"
                f"🚀 Pásate por los canales de **comunidad** y disfruta de la estadía."
            ),
            color=discord.Color.blue()
        )
        
        # Muestra el avatar del usuario que acaba de entrar
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Eres el miembro #{total_miembros} del servidor")

        await canal.send(content=f"🎉 ¡Bienvenido/a {member.mention}!", embed=embed)

async def setup(bot):
    await bot.add_cog(BienvenidasEmbed(bot))