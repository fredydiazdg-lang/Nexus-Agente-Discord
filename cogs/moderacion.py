import discord
from discord.ext import commands

class Moderacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, miembro: discord.Member, *, razon="No especificada"):
        await miembro.kick(reason=razon)
        await ctx.send(f"👞 **{miembro.display_name}** ha sido expulsado. Razón: {razon}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, miembro: discord.Member, *, razon="No especificada"):
        await miembro.ban(reason=razon)
        await ctx.send(f"🔨 **{miembro.display_name}** ha sido baneado permanentemente. Razón: {razon}")

    @commands.command(name="limpiar")
    @commands.has_permissions(manage_messages=True)
    async def limpiar(self, ctx, cantidad: int = 10):
        await ctx.channel.purge(limit=cantidad + 1)
        msg = await ctx.send(f"🧹 NEXUS eliminó **{cantidad}** mensajes.")
        await msg.delete(delay=4)

async def setup(bot):
    await bot.add_cog(Moderacion(bot))