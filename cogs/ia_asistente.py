import discord
from discord.ext import commands
import re

class IAAsistente(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def es_canal_maestro_ia(self, nombre_canal: str) -> bool:
        # Limpiar emojis, símbolos y convertir a minúsculas
        nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '', nombre_canal).lower()
        # Detecta si el canal contiene 'maestro' e 'ia' sin importar los emojis o fuentes estéticas
        return "maestro" in nombre_limpio and "ia" in nombre_limpio

    def generar_respuesta_inteligente(self, pregunta: str, usuario: str) -> str:
        p = pregunta.lower()

        # Preguntas sobre Free Fire y Torneos / Cuentas
        if any(w in p for w in ["torneo", "inscripcion", "duelo", "4v4", "1v1", "sala", "cuenta", "compra", "venta"]):
            return (
                f"¡Hola {usuario}! Para torneos, duelos o información sobre compra/venta de cuentas, "
                "por favor revisa las secciones de anuncios o abre un ticket en nuestro centro de atención privada."
            )
        
        # Preguntas sobre Economía y Monedas
        elif any(w in p for w in ["monedas", "diamantes", "economia", "comprar", "vip", "cartera", "bal"]):
            return (
                f"¡Hola {usuario}! Puedes ganar Monedas Nexus jugando con `!trabajar`, "
                "reclamando tu bono diario con `!diario` o apostando en la `!ruleta`. "
                "Revisa tu saldo con `!cartera` o adquiere el rango VIP con `!comprar vip`."
            )

        # Preguntas sobre Clips y Comunidad
        elif any(w in p for w in ["clip", "video", "tiktok", "jugada", "headshot"]):
            return (
                f"¡Hey {usuario}! Sube tus mejores jugadas al canal de `#clips-comunidad`. "
                "NEXUS le agregará botones de votación para que todos califiquen tus mejores jugadas. 🔥"
            )

        # Preguntas sobre Ayuda / Comandos Generales
        elif any(w in p for w in ["ayuda", "comandos", "bot", "que haces", "nexus"]):
            return (
                f"Soy **Maestro IA**, el asistente inteligente oficial de la comunidad. "
                "Escribe aquí cualquier duda que tengas sobre reglas, economía, compras o torneos y te responderé de inmediato."
            )

        # Respuesta general por defecto
        else:
            return (
                f"Gracias por tu pregunta, {usuario}. Procesé tu consulta sobre: *'{pregunta}'*.\n\n"
                "Si necesitas ayuda directa del Staff, puedes abrir un ticket de soporte. "
                "¡Estoy listo en este canal de **Maestro IA** para cualquier otra duda!"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Verificar si es el canal Maestro IA o si etiquetaron al bot directamente
        es_canal_ia = self.es_canal_maestro_ia(message.channel.name)
        menciono_bot = self.bot.user in message.mentions

        if es_canal_ia or menciono_bot:
            # Eliminar la mención del texto si la hay
            contenido = message.content.replace(f"<@{self.bot.user.id}>", "").strip()

            if not contenido:
                await message.reply("🤖 ¡Hola! Soy **Maestro IA**. Escribe tu pregunta aquí y te responderé al instante.")
                return

            async with message.channel.typing():
                respuesta = self.generar_respuesta_inteligente(contenido, message.author.display_name)

                embed = discord.Embed(
                    title="🧠 MAESTRO IA | Respuestas",
                    description=respuesta,
                    color=discord.Color.purple()
                )
                embed.set_footer(text="NEXUS Agent System • Maestro IA")

                await message.reply(embed=embed)

    @commands.command(name="ia", aliases=["preguntar", "maestro"])
    async def ia_comando(self, ctx, *, pregunta: str):
        async with ctx.channel.typing():
            respuesta = self.generar_respuesta_inteligente(pregunta, ctx.author.display_name)

            embed = discord.Embed(
                title="🧠 MAESTRO IA | Respuestas",
                description=respuesta,
                color=discord.Color.purple()
            )
            embed.set_footer(text="NEXUS Agent System • Maestro IA")

            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IAAsistente(bot))