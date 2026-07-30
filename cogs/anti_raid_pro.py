import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

# Configuración de límites (ajustable según la velocidad que quieras)
MAX_CANALES_BORRADOS = 3
MAX_BANEO_MASIVO = 3
TIEMPO_VENTANA_SEGUNDOS = 10

class AntiRaidPro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Historiales en memoria para medir la velocidad de las acciones
        self.canales_borrados = {}
        self.baneos_realizados = {}

    async def quitar_permisos_peligrosos(self, usuario, guild, razon):
        """Le quita todos los roles con permisos administrativos o de moderación al atacante."""
        roles_a_quitar = []
        for rol in usuario.roles:
            if rol.permissions.administrator or rol.permissions.manage_channels or rol.permissions.ban_members:
                roles_a_quitar.append(rol)

        if roles_a_quitar:
            try:
                await usuario.remove_roles(*roles_a_quitar, reason=f"NEXUS ANTI-RAID: {razon}")
            except Exception:
                pass

        # Registrar el incidente en el canal de logs
        canal_logs = discord.utils.get(guild.text_channels, name="logs") or discord.utils.get(guild.text_channels, name="auditoria")
        if canal_logs:
            embed = discord.Embed(
                title="🚨 ¡ALERTA MÁXIMA ANTI-RAID / ANTI-NUKE!",
                description=f"**Usuario sospechoso:** {usuario.mention} (`{usuario.id}`)\n**Acción tomada:** Se le retiraron los permisos de moderación/administración de inmediato.\n**Razon:** {razon}",
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=usuario.display_avatar.url)
            await canal_logs.send(embed=embed)

    # 1. ANTI-NUKE DE CANALES (Si borran múltiples canales seguidos)
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        ahora = datetime.now()

        # Buscar en el registro de auditoría de Discord quién borró el canal
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            usuario = entry.user
            if usuario.id == self.bot.user.id or usuario.id == guild.owner_id:
                return  # Ignorar si es el bot o el dueño del servidor

            uid = usuario.id
            if uid not in self.canales_borrados:
                self.canales_borrados[uid] = []

            # Filtrar registros dentro del rango de tiempo
            self.canales_borrados[uid] = [t for t in self.canales_borrados[uid] if ahora - t < timedelta(seconds=TIEMPO_VENTANA_SEGUNDOS)]
            self.canales_borrados[uid].append(ahora)

            if len(self.canales_borrados[uid]) >= MAX_CANALES_BORRADOS:
                await self.quitar_permisos_peligrosos(
                    usuario, 
                    guild, 
                    f"Eliminó {len(self.canales_borrados[uid])} canales en menos de {TIEMPO_VENTANA_SEGUNDOS} segundos."
                )
                self.canales_borrados[uid] = []

    # 2. ANTI-BANEO MASIVO (Si expulsan/banean a la comunidad rápidamente)
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        ahora = datetime.now()

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            usuario = entry.user
            if usuario.id == self.bot.user.id or usuario.id == guild.owner_id:
                return

            uid = usuario.id
            if uid not in self.baneos_realizados:
                self.baneos_realizados[uid] = []

            self.baneos_realizados[uid] = [t for t in self.baneos_realizados[uid] if ahora - t < timedelta(seconds=TIEMPO_VENTANA_SEGUNDOS)]
            self.baneos_realizados[uid].append(ahora)

            if len(self.baneos_realizados[uid]) >= MAX_BANEO_MASIVO:
                await self.quitar_permisos_peligrosos(
                    usuario, 
                    guild, 
                    f"Ejecutó {len(self.baneos_realizados[uid])} baneos en menos de {TIEMPO_VENTANA_SEGUNDOS} segundos."
                )
                self.baneos_realizados[uid] = []

async def setup(bot):
    await bot.add_cog(AntiRaidPro(bot))