import discord
from discord.ext import commands

class NotificacionesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔔 Alertas de Anuncios", style=discord.ButtonStyle.primary, custom_id="rol_anuncios")
    async def btn_anuncios(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_rol(interaction, "Notificaciones")

    @discord.ui.button(label="🎮 Alertas de Eventos/Torneos", style=discord.ButtonStyle.success, custom_id="rol_torneos")
    async def btn_torneos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_rol(interaction, "Torneos")

    async def toggle_rol(self, interaction: discord.Interaction, nombre_rol: str):
        guild = interaction.guild
        rol = discord.utils.get(guild.roles, name=nombre_rol)
        if not rol:
            await interaction.response.send_message(f"❌ El rol **{nombre_rol}** no existe en el servidor. Créalo en los ajustes de Discord.", ephemeral=True)
            return

        if rol in interaction.user.roles:
            await interaction.user.remove_roles(rol)
            await interaction.response.send_message(f"🔕 Ya no recibirás alertas de **{nombre_rol}**.", ephemeral=True)
        else:
            await interaction.user.add_roles(rol)
            await interaction.response.send_message(f"🔔 Te has suscrito a las alertas de **{nombre_rol}**.", ephemeral=True)

class AutoRolesTemp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel_alertas")
    @commands.has_permissions(administrator=True)
    async def panel_alertas(self, ctx):
        embed = discord.Embed(
            title="🔔 CONFIGURACIÓN DE NOTIFICACIONES",
            description="Elige qué avisos quieres recibir en tu cuenta presionando los botones:",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=NotificacionesView())

async def setup(bot):
    await bot.add_cog(AutoRolesTemp(bot))