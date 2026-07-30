import discord
from discord.ext import commands

class VerificacionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛡️ Verificarme y Obtener Acceso", style=discord.ButtonStyle.success, custom_id="btn_verificacion_pro")
    async def verificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        
        # Busca el rol 'Verificado' o 'Miembro'
        rol_verificado = discord.utils.get(guild.roles, name="Verificado") or discord.utils.get(guild.roles, name="Miembro")

        # Si no existe ninguno, el bot lo crea automáticamente
        if not rol_verificado:
            try:
                rol_verificado = await guild.create_role(name="Miembro", color=discord.Color.green(), reason="Rol auto-creado por verificación")
            except Exception as e:
                await interaction.response.send_message(f"⚠️ El bot no tiene permisos para crear roles en el servidor: {e}", ephemeral=True)
                return

        if rol_verificado in interaction.user.roles:
            await interaction.response.send_message("✅ Ya cuentas con la verificación ejecutiva en este servidor.", ephemeral=True)
            return

        try:
            await interaction.user.add_roles(rol_verificado)
            await interaction.response.send_message("🎉 ¡Verificación completada con éxito! Se te ha otorgado acceso total al servidor.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ El rol del bot debe estar por encima del rol 'Miembro' en los Ajustes de Servidor > Roles: {e}", ephemeral=True)

class Verificacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel_verificacion")
    @commands.has_permissions(administrator=True)
    async def panel_verificacion(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(
            title="🛡️ PORTAL DE SEGURIDAD Y VERIFICACIÓN",
            description=(
                "Bienvenido/a a la comunidad. Para mantener un entorno seguro y libre de bots maliciosos, "
                "requerimos confirmación de identidad humana.\n\n"
                "📌 **Instrucciones:**\n"
                "Haz clic en el botón inferior para validar tu cuenta y desbloquear todos los canales del servidor."
            ),
            color=discord.Color.blue()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="NEXUS Executive Security System")

        await ctx.send(embed=embed, view=VerificacionView())

async def setup(bot):
    await bot.add_cog(Verificacion(bot))