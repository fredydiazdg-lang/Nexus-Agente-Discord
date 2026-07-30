import discord
from discord.ext import commands

NOMBRE_ROL_VERIFICADO = "Verificado"  # El bot creará este rol solo si no existe

class BotonVerificacion(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verificarse", style=discord.ButtonStyle.green, custom_id="btn_verificar_nexus_auto")
    async def verificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        # Buscar el rol o crearlo automáticamente
        rol = discord.utils.get(guild.roles, name=NOMBRE_ROL_VERIFICADO)
        
        if not rol:
            rol = await guild.create_role(name=NOMBRE_ROL_VERIFICADO, color=discord.Color.green(), reason="Rol creado automáticamente por NEXUS")

        if rol in interaction.user.roles:
            await interaction.response.send_message("⚠️ ¡Ya estás verificado en el servidor!", ephemeral=True)
        else:
            await interaction.user.add_roles(rol)
            await interaction.response.send_message("🎉 ¡Te has verificado correctamente! Bienvenido.", ephemeral=True)

class PanelVerificacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="enviarverificacion")
    @commands.has_permissions(administrator=True)
    async def enviarverificacion(self, ctx):
        embed = discord.Embed(
            title="🛡️ VERIFICACIÓN DEL SERVIDOR",
            description="Haz clic en el botón de abajo para verificarte y obtener acceso completo al servidor.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="NEXUS Security System")
        await ctx.send(embed=embed, view=BotonVerificacion())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(PanelVerificacion(bot))