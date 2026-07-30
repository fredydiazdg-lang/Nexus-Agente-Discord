import discord
from discord.ext import commands

class ModalReporte(discord.ui.Modal, title="📝 Formulario Oficial de Reporte"):
    usuario_reportado = discord.ui.TextInput(
        label="Usuario a reportar (Nombre o ID)",
        placeholder="Ejemplo: @UsuarioToxico o ID",
        required=True
    )
    motivo = discord.ui.TextInput(
        label="Motivo del reporte",
        style=discord.TextStyle.paragraph,
        placeholder="Describe detalladamente lo sucedido...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        canal_reportes = discord.utils.get(interaction.guild.text_channels, name="reportes-staff") or discord.utils.get(interaction.guild.text_channels, name="logs")

        if not canal_reportes:
            await interaction.response.send_message("❌ No se encontró un canal llamado `#reportes-staff` para procesar tu solicitud.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🚨 NUEVO REPORTE RECIBIDO",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Autor del Reporte", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="⚠️ Usuario Reportado", value=f"`{self.usuario_reportado.value}`", inline=False)
        embed.add_field(name="📄 Detalles / Motivo", value=f"{self.motivo.value}", inline=False)
        embed.set_footer(text=f"NEXUS System • Fecha de emisión")

        await canal_reportes.send(embed=embed)
        await interaction.response.send_message("✅ Tu reporte ha sido enviado de forma confidencial al equipo de administración.", ephemeral=True)

class ReporteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📢 Iniciar Reporte", style=discord.ButtonStyle.danger, custom_id="btn_abrir_reporte")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalReporte())

class Reportes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel_reportes")
    @commands.has_permissions(administrator=True)
    async def panel_reportes(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(
            title="📢 CENTRO DE REPORTES Y DENUNCIAS",
            description="Si presenciaste una infracción a las normas del servidor, acoso o conducta inapropiada, utiliza el formulario confidencial.",
            color=discord.Color.dark_red()
        )
        embed.set_footer(text="Los reportes son revisados estrictamente por el Staff.")
        await ctx.send(embed=embed, view=ReporteView())

async def setup(bot):
    await bot.add_cog(Reportes(bot))