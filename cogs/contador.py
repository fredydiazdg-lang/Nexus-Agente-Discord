import discord
from discord.ext import commands

class Contador(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def actualizar_contador(self, guild):
        canal = discord.utils.get(guild.voice_channels, name=lambda n: n and n.startswith("👥 Miembros:"))
        total = guild.member_count

        if not canal:
            # Crear canal de voz bloqueado si no existe
            overwrites = {guild.default_role: discord.PermissionOverwrite(connect=False)}
            canal = await guild.create_voice_channel(f"👥 Miembros: {total}", overwrites=overwrites, position=0)
        else:
            await canal.edit(name=f"👥 Miembros: {total}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.actualizar_contador(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.actualizar_contador(member.guild)

async def setup(bot):
    await bot.add_cog(Contador(bot))