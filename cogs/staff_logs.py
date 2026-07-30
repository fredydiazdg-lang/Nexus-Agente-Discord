import discord
from discord.ext import commands

class StaffLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        # Escucha directamente los registros de auditoría internos de Discord
        guild = entry.guild
        canal_audit = discord.utils.get(guild.text_channels, name="auditoria-staff") or discord.utils.get(guild.text_channels, name="logs")

        if not canal_audit:
            return

        embed = None

        # Expulsión (Kick)
        if entry.action == discord.AuditLogAction.kick:
            embed = discord.Embed(title="🛡️ AUDITORÍA STAFF: Expulsión", color=discord.Color.orange())
            embed.add_field(name="👑 Moderador Responsable", value=f"{entry.user.mention}", inline=True)
            embed.add_field(name="👤 Usuario Afectado", value=f"{entry.target.mention}", inline=True)
            embed.add_field(name="📝 Razón", value=f"`{entry.reason or 'Sin razón especificada'}`", inline=False)

        # Ban
        elif entry.action == discord.AuditLogAction.ban_add:
            embed = discord.Embed(title="🔨 AUDITORÍA STAFF: Baneo Permanente", color=discord.Color.dark_red())
            embed.add_field(name="👑 Moderador Responsable", value=f"{entry.user.mention}", inline=True)
            embed.add_field(name="👤 Usuario Afectado", value=f"{entry.target.mention}", inline=True)
            embed.add_field(name="📝 Razón", value=f"`{entry.reason or 'Sin razón especificada'}`", inline=False)

        # Eliminación masiva de mensajes
        elif entry.action == discord.AuditLogAction.message_bulk_delete:
            embed = discord.Embed(title="🧹 AUDITORÍA STAFF: Limpieza de Mensajes", color=discord.Color.blue())
            embed.add_field(name="👑 Moderador Responsable", value=f"{entry.user.mention}", inline=True)
            embed.add_field(name="📍 Canal Afectado", value=f"{entry.extra.channel.mention}", inline=True)
            embed.add_field(name="📊 Cantidad de Mensajes", value=f"`{entry.extra.count}`", inline=False)

        if embed:
            embed.set_footer(text=f"ID de Acción: {entry.id}")
            await canal_audit.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StaffLogs(bot))