import discord
from discord.ext import commands

class Anuncios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="anuncio")
    @commands.has_permissions(administrator=True)
    async def anuncio(self, ctx, titulo: str, mensaje: str, url_imagen: str = None):
        # Intentar borrar el mensaje del comando
        try:
            await ctx.message.delete()
        except Exception:
            pass

        # Crear el Embed elegante
        embed = discord.Embed(
            title=f"📢 {titulo.upper()}",
            description=f"\n{mensaje}\n",
            color=discord.Color.gold()
        )

        # Encabezado del Servidor
        if ctx.guild.icon:
            embed.set_author(name=f"COMUNICADO OFICIAL • {ctx.guild.name}", icon_url=ctx.guild.icon.url)
        else:
            embed.set_author(name=f"COMUNICADO OFICIAL • {ctx.guild.name}")

        # Si le pasas un enlace de imagen/GIF, lo coloca como Banner grande
        if url_imagen:
            embed.set_image(url=url_imagen)

        # Pie de página con tu avatar y nombre
        embed.set_footer(
            text=f"Publicado por {ctx.author.display_name} • NEXUS Admin",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Anuncios(bot))