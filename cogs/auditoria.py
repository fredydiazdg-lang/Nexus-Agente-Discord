import discord
from discord.ext import commands
from datetime import datetime

# Nombre del canal donde NEXUS enviará todos los registros de auditoría
NOMBRE_CANAL_LOGS = "logs"

class Auditoria(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def obtener_canal_logs(self, guild):
        canal = discord.utils.get(guild.text_channels, name=NOMBRE_CANAL_LOGS)
        if not canal:
            canal = discord.utils.get(guild.text_channels, name="auditoria")
        if not canal:
            # Crear canal de logs si no existe
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False)
            }
            for rol in guild.roles:
                if rol.permissions.administrator:
                    overwrites[rol] = discord.PermissionOverwrite(read_messages=True)
            try:
                canal = await guild.create_text_channel(NOMBRE_CANAL_LOGS, overwrites=overwrites, reason="Canal de auditoría para NEXUS")
            except Exception:
                return None
        return canal

    # 1. MENSAJES EDITADOS
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        canal = await self.obtener_canal_logs(before.guild)
        if not canal:
            return

        embed = discord.Embed(
            title="✏️ Mensaje Editado",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
        embed.add_field(name="Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="Antes", value=before.content or "*Sin contenido*", inline=False)
        embed.add_field(name="Ahora", value=after.content or "*Sin contenido*", inline=False)
        embed.set_footer(text=f"ID Usuario: {before.author.id}")

        await canal.send(embed=embed)

    # 2. MENSAJES ELIMINADOS
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        canal = await self.obtener_canal_logs(message.guild)
        if not canal:
            return

        embed = discord.Embed(
            title="🗑️ Mensaje Eliminado",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenido", value=message.content or "*Sin contenido o archivo multimedia*", inline=False)
        embed.set_footer(text=f"ID Usuario: {message.author.id}")

        await canal.send(embed=embed)

    # 3. REGISTRO DE VOZ (ENTRADAS, SALIDAS Y CAMBIOS DE CANAL)
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        canal = await self.obtener_canal_logs(member.guild)
        if not canal:
            return

        # Se conectó a voz
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🎙️ Conexión a Voz",
                description=f"**{member.mention}** se conectó al canal {after.channel.mention}",
                color=discord.Color.green()
            )
            await canal.send(embed=embed)

        # Se desconectó de voz
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🔇 Desconexión de Voz",
                description=f"**{member.mention}** salió del canal **{before.channel.name}**",
                color=discord.Color.dark_grey()
            )
            await canal.send(embed=embed)

        # Cambió de canal de voz
        elif before.channel != after.channel and before.channel is not None and after.channel is not None:
            embed = discord.Embed(
                title="🔀 Cambio de Canal de Voz",
                description=f"**{member.mention}** se movió de **{before.channel.name}** a {after.channel.mention}",
                color=discord.Color.blurple()
            )
            await canal.send(embed=embed)

    # 4. ENTRADA DE MIEMBROS (ANTIGÜEDAD DE LA CUENTA / DETECCIÓN DE BOTS FALSOS)
    @commands.Cog.listener()
    async def on_member_join(self, member):
        canal = await self.obtener_canal_logs(member.guild)
        if not canal:
            return

        # Calcular antigüedad de la cuenta
        creacion = member.created_at.replace(tzinfo=None)
        dias_antiguedad = (datetime.now() - creacion).days

        es_sospechosa = dias_antiguedad < 7  # Si tiene menos de 7 días de creada

        color = discord.Color.orange() if es_sospechosa else discord.Color.blue()
        alerta = " ⚠️ **¡CUENTA NUEVA / SOSPECHOSA!**" if es_sospechosa else ""

        embed = discord.Embed(
            title=f"📥 Nuevo Miembro Unid@{alerta}",
            description=f"{member.mention} (`{member.name}`)",
            color=color,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Antigüedad de la Cuenta", value=f"`{dias_antiguedad} días` (Creada el {creacion.strftime('%d/%m/%Y')})", inline=False)
        embed.set_footer(text=f"ID Usuario: {member.id}")

        await canal.send(embed=embed)

    # 5. SALIDA DE MIEMBROS
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        canal = await self.obtener_canal_logs(member.guild)
        if not canal:
            return

        embed = discord.Embed(
            title="📤 Miembro Salió del Servidor",
            description=f"**{member.display_name}** (`{member.name}`) ha abandonado el servidor.",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID Usuario: {member.id}")

        await canal.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Auditoria(bot))