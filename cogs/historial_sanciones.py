import discord
from discord.ext import commands
import json
import os

ARCHIVO_HISTORIAL = "historial_sanciones.json"

class HistorialSanciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.datos = self.cargar_datos()

    def cargar_datos(self):
        if os.path.exists(ARCHIVO_HISTORIAL):
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def guardar_datos(self):
        with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, indent=4, ensure_ascii=False)

    @commands.command(name="warn", aliases=["advertir"])
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, usuario: discord.Member, *, razon: str = "Sin razón especificada"):
        user_id = str(usuario.id)
        
        if user_id not in self.datos:
            self.datos[user_id] = []

        inf = {
            "moderador": ctx.author.display_name,
            "razon": razon
        }
        self.datos[user_id].append(inf)
        self.guardar_datos()

        total = len(self.datos[user_id])
        
        embed = discord.Embed(
            title="⚠️ Advertencia Registrada",
            description=f"**Usuario:** {usuario.mention}\n**Razón:** {razon}\n**Total de infracciones:** `{total}`",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Sancionado por {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name="infracciones", aliases=["historial", "warns"])
    @commands.has_permissions(manage_messages=True)
    async def infracciones(self, ctx, usuario: discord.Member):
        user_id = str(usuario.id)
        registros = self.datos.get(user_id, [])

        if not registros:
            await ctx.send(f"✅ **{usuario.display_name}** no tiene ninguna advertencia o sanción registrada.")
            return

        embed = discord.Embed(
            title=f"📜 Historial de Sanciones de {usuario.display_name}",
            color=discord.Color.red()
        )
        for idx, inf in enumerate(registros, 1):
            embed.add_field(
                name=f"Infracción #{idx}",
                value=f"📌 **Razón:** {inf['razon']}\n🛡️ **Staff:** {inf['moderador']}",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HistorialSanciones(bot))