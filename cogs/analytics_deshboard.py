import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

class AnalyticsDashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_dir = "stats_data"
        if not os.path.exists(self.stats_dir):
            os.makedirs(self.stats_dir)

    def _get_guild_file(self, guild_id):
        return os.path.join(self.stats_dir, f"stats_{guild_id}.json")

    def _load_stats(self, guild_id):
        file_path = self._get_guild_file(guild_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"total_messages": 0, "active_users": {}, "hourly_activity": {str(i): 0 for i in range(24)}}

    def _save_stats(self, guild_id, data):
        file_path = self._get_guild_file(guild_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        data = self._load_stats(guild_id)

        # Contador global de mensajes
        data["total_messages"] += 1

        # Contador de mensajes por usuario
        user_id = str(message.author.id)
        data["active_users"][user_id] = data["active_users"].get(user_id, 0) + 1

        # Registro por hora pico (00 a 23)
        hora_actual = str(datetime.now().hour)
        data["hourly_activity"][hora_actual] = data["hourly_activity"].get(hora_actual, 0) + 1

        self._save_stats(guild_id, data)

    analytics_group = app_commands.Group(name="stats", description="Analítica y salud del servidor")

    @analytics_group.command(name="resumen", description="Muestra el panel general de estadísticas del servidor")
    async def stats_resumen(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild
        data = self._load_stats(guild.id)

        # Top 3 usuarios más activos
        top_usuarios = sorted(data["active_users"].items(), key=lambda x: x[1], reverse=True)[:3]
        top_txt = ""
        for i, (u_id, count) in enumerate(top_usuarios, 1):
            member = guild.get_member(int(u_id))
            nombre = member.mention if member else f"Usuario ({u_id})"
            top_txt += f"`{i}.` {nombre} — **{count}** mensajes\n"

        if not top_txt:
            top_txt = "*Aún no hay datos de mensajes registrados.*"

        # Determinación de la hora pico de actividad
        hora_pico = max(data["hourly_activity"], key=data["hourly_activity"].get)
        mensajes_hora_pico = data["hourly_activity"][hora_pico]

        embed = discord.Embed(
            title=f"📊 Analítica de Comunidad — {guild.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="👥 Total de Miembros:", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="💬 Mensajes Registrados:", value=f"`{data['total_messages']}`", inline=True)
        embed.add_field(name="🔥 Hora Pico del Servidor:", value=f"`{hora_pico}:00 hrs` ({mensajes_hora_pico} msgs)", inline=True)
        embed.add_field(name="🏆 Top Usuarios Más Activos:", value=top_txt, inline=False)
        embed.set_footer(text="Nexus Analytics Engine • Datos actualizados en tiempo real")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AnalyticsDashboard(bot))