import discord
from discord.ext import commands

class EncuestaView(discord.ui.View):
    def __init__(self, opcion1, opcion2):
        super().__init__(timeout=None)
        self.votos_1 = 0
        self.votos_2 = 0
        self.opcion1 = opcion1
        self.opcion2 = opcion2
        self.usuarios_votaron = []

    @discord.ui.button(label="Opción A", style=discord.ButtonStyle.primary, custom_id="voto_opt1")
    async def boton_opt1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.usuarios_votaron:
            await interaction.response.send_message("⚠️ Ya has emitido tu voto en esta encuesta.", ephemeral=True)
            return

        self.votos_1 += 1
        self.usuarios_votaron.append(interaction.user.id)
        await interaction.response.send_message(f"✅ Votaste por: **{self.opcion1}**", ephemeral=True)
        await self.actualizar_embed(interaction)

    @discord.ui.button(label="Opción B", style=discord.ButtonStyle.success, custom_id="voto_opt2")
    async def boton_opt2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.usuarios_votaron:
            await interaction.response.send_message("⚠️ Ya has emitido tu voto en esta encuesta.", ephemeral=True)
            return

        self.votos_2 += 1
        self.usuarios_votaron.append(interaction.user.id)
        await interaction.response.send_message(f"✅ Votaste por: **{self.opcion2}**", ephemeral=True)
        await self.actualizar_embed(interaction)

    async def actualizar_embed(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name=f"🅰️ {self.opcion1}", value=f"**{self.votos_1}** votos", inline=True)
        embed.set_field_at(1, name=f"🅱️ {self.opcion2}", value=f"**{self.votos_2}** votos", inline=True)
        await interaction.message.edit(embed=embed)


class Encuestas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="encuesta")
    @commands.has_permissions(administrator=True)
    async def encuesta(self, ctx, pregunta: str, opcion1: str, opcion2: str):
        embed = discord.Embed(
            title="📊 ENCUESTA OFICIAL DE LA COMUNIDAD",
            description=f"**Pregunta:** {pregunta}\n\nHaz clic en los botones de abajo para votar:",
            color=discord.Color.blue()
        )
        embed.add_field(name=f"🅰️ {opcion1}", value="**0** votos", inline=True)
        embed.add_field(name=f"🅱️ {opcion2}", value="**0** votos", inline=True)
        embed.set_footer(text=f"Encuesta iniciada por {ctx.author.display_name}")

        view = EncuestaView(opcion1, opcion2)
        view.children[0].label = f"Votar A: {opcion1}"
        view.children[1].label = f"Votar B: {opcion2}"

        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Encuestas(bot))