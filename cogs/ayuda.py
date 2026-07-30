import discord
from discord.ext import commands

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛡️ Moderación", description="Kick, Ban, Limpiar, AutoMod", value="mod"),
            discord.SelectOption(label="💰 Economía", description="Cartera, Trabajar, Ruleta, Robar", value="eco"),
            discord.SelectOption(label="🎮 Trivias & IA", description="Preguntas, Retos Visuales y Groq IA", value="trivia"),
            discord.SelectOption(label="🎵 Música & Voz", description="Play, Join, Leave y Salas Dinámicas", value="musica"),
            discord.SelectOption(label="🎫 Tickets & Ayuda", description="Soporte, Sugerencias y Anuncios", value="soporte"),
        ]
        super().__init__(placeholder="Elegir categoría de comandos...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "mod":
            desc = "**Comandos de Moderación:**\n`!kick @user` - Expulsar miembro\n`!ban @user` - Banear miembro\n`!limpiar 10` - Borrar mensajes\n`AutoMod` - Filtro activo 24/7"
        elif self.values[0] == "eco":
            desc = "**Comandos de Economía:**\n`!bal` - Ver tus monedas\n`!trabajar` - Ganar monedas gratis\n`!ruleta 100 rojo` - Apostar en casino\n`!robar @user` - Intentar un robo"
        elif self.values[0] == "trivia":
            desc = "**Comandos de Entrenamiento:**\n`!trivia` - Retos visuales y preguntas con XP\n`Mención al Bot` - Hablar con la IA inteligente"
        elif self.values[0] == "musica":
            desc = "**Comandos de Música & Voz:**\n`!join` - Unir bot a tu canal\n`!play [cancion]` - Reproducir música\n`!leave` - Desconectar bot"
        elif self.values[0] == "soporte":
            desc = "**Soporte y Utilidades:**\n`!panel_tickets` - Crear panel de ayuda\n`!sugerir [idea]` - Enviar sugerencia\n`!anuncio` - Comunicados oficiales"

        embed = discord.Embed(title="📚 GUÍA DE COMANDOS DE NEXUS", description=desc, color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpSelect())

class PanelAyuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ayuda", aliases=["help", "comandos"])
    async def ayuda(self, ctx):
        embed = discord.Embed(
            title="👑 PANORAMA GENERAL DE NEXUS",
            description="Bienvenido al centro de control de NEXUS. Selecciona una categoría en el menú desplegable de abajo para explorar todos mis poderes:",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed, view=HelpView())

async def setup(bot):
    await bot.add_cog(PanelAyuda(bot))