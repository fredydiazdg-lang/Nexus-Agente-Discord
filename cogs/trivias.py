import os
import random
import discord
from discord.ext import commands
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class TriviaView(discord.ui.View):
    def __init__(self, respuesta_correcta):
        super().__init__(timeout=20.0)
        self.respuesta_correcta = respuesta_correcta
        self.ganador = None

    async def procesar_respuesta(self, interaction: discord.Interaction, eleccion: str):
        if self.ganador:
            await interaction.response.send_message("❌ Esta trivia ya fue resuelta.", ephemeral=True)
            return

        if eleccion.lower() == self.respuesta_correcta.lower():
            self.ganador = interaction.user
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"🎉 ¡Excelente {interaction.user.mention}! Respuesta CORRECTA.")
            self.stop()
        else:
            await interaction.response.send_message("❌ ¡Respuesta incorrecta!", ephemeral=True)

    @discord.ui.button(label="Opción A", style=discord.ButtonStyle.primary)
    async def boton_a(self, interaction, button):
        await self.procesar_respuesta(interaction, button.label)

    @discord.ui.button(label="Opción B", style=discord.ButtonStyle.primary)
    async def boton_b(self, interaction, button):
        await self.procesar_respuesta(interaction, button.label)

    @discord.ui.button(label="Opción C", style=discord.ButtonStyle.primary)
    async def boton_c(self, interaction, button):
        await self.procesar_respuesta(interaction, button.label)

    @discord.ui.button(label="Opción D", style=discord.ButtonStyle.primary)
    async def boton_d(self, interaction, button):
        await self.procesar_respuesta(interaction, button.label)


TRIVIAS_VISUALES = [
    {
        "pregunta": "🧠 CAPCIOSA: Si un avión se estrella en la frontera España-Francia, ¿dónde entierran a los supervivientes?",
        "imagen": "https://media.giphy.com/media/3o7TKsjLu9P9G6oI3C/giphy.gif",
        "opciones": ["En España", "En Francia", "En la frontera", "En ningún lado"],
        "correcta": "En ningún lado"
    },
    {
        "pregunta": "🎮 FREE FIRE: ¿Qué mapa clásico representa esta zona?",
        "imagen": "https://www.u7buy.com/blog/wp-content/uploads/2024/11/1.5-1.png",  
        "opciones": ["Bermuda", "Purgatorio", "Kalahari", "Alpes"],
        "correcta": "Bermuda"
    },
    {
        "pregunta": "🎮 FREE FIRE: ¿Cuál personaje posee la habilidad 'Ritmo Brutal'?",
        "imagen": "https://cdn.discordapp.com/attachments/1528058099036983446/1532012996195516446/1c37c6430e1eb1ca2f3a4e6ebdf760a8.png?ex=6a6b4dc9&is=6a69fc49&hm=5989a98af4c071478ef5953f1d042947efe3b7c6dc9cd501302c0051a4c8a209&",
        "opciones": ["Alok", "Chrono", "Kelly", "Kenta"],
        "correcta": "Alok"
    },
    {
        "pregunta": "🎮 FREE FIRE: ¿Cuál es el mapa de desierto?",
        "imagen": "https://cdn.discordapp.com/attachments/1528058099036983446/1532013601173278820/c8efc49bd4b578f99cfac378d608ce1a.png?ex=6a6b4e59&is=6a69fcd9&hm=a0c3fb963c1454a2c6bc1116bec1ed648e125b420be20705c5488ebf66068e77&",
        "opciones": ["Bermuda", "Kalahari", "Purgatorio", "Nexterra"],
        "correcta": "Kalahari"
    }
]

class Trivias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recientes = []

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.bot.user.mentioned_in(message) and groq_client:
            async with message.channel.typing():
                try:
                    texto = message.content.replace(f'<@{self.bot.user.id}>', '').strip() or "Hola"
                    resp = groq_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "Eres NEXUS, el bot administrador absoluto del servidor. Responde directo, gamer y genial en español."},
                            {"role": "user", "content": texto}
                        ],
                        model="llama-3.1-8b-instant"
                    )
                    await message.reply(resp.choices[0].message.content)
                except Exception as e:
                    print(f"Error IA: {e}")

    @commands.command(name="trivia")
    async def trivia(self, ctx):
        disponibles = [q for q in TRIVIAS_VISUALES if q['pregunta'] not in self.recientes]
        if not disponibles:
            self.recientes.clear()
            disponibles = TRIVIAS_VISUALES

        item = random.choice(disponibles)
        self.recientes.append(item['pregunta'])

        embed = discord.Embed(
            title="🎮 TRIVIA & RETO VISUAL NEXUS",
            description=f"**{item['pregunta']}**",
            color=discord.Color.gold()
        )
        if item['imagen']:
            embed.set_image(url=item['imagen'])

        view = TriviaView(respuesta_correcta=item['correcta'])
        for i, child in enumerate(view.children):
            child.label = item['opciones'][i]

        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Trivias(bot))