import discord
from discord.ext import commands, tasks

class EstadisticasServidor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actualizar_stats.start()

    def cog_unload(self):
        self.actualizar_stats.cancel()

    @tasks.loop(minutes=10)
    async def actualizar_stats(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            total_miembros = guild.member_count
            
            # Buscar canales por nombre estricto para actualizar contadores
            for channel in guild.voice_channels:
                if "👥 Miembros:" in channel.name:
                    try:
                        await channel.edit(name=f"👥 Miembros: {total_miembros}")
                    except Exception:
                        pass

    @commands.command(name="crearstats")
    @commands.has_permissions(administrator=True)
    async def crearstats(self, ctx):
        guild = ctx.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True)
        }
        
        # Crea el canal de voz estático informativo
        await guild.create_voice_channel(name=f"👥 Miembros: {guild.member_count}", overwrites=overwrites)
        await ctx.send("✅ ¡Canal de estadística de miembros creado con éxito!", delete_after=5)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(EstadisticasServidor(bot))