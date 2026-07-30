import discord
from discord.ext import commands
import json
import os

ARCHIVO_ECONOMIA = "economia.json"

class SistemaEconomiaAvanzado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.cargar_datos()

    def cargar_datos(self):
        if os.path.exists(ARCHIVO_ECONOMIA):
            with open(ARCHIVO_ECONOMIA, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def guardar_datos(self):
        with open(ARCHIVO_ECONOMIA, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    @commands.command(name="cartera", aliases=["bal", "balance", "monedas"])
    async def cartera(self, ctx, miembro: discord.Member = None):
        target = miembro or ctx.author
        user_id = str(target.id)
        bal = self.data.get(user_id, {}).get("coins", 500)
        
        embed = discord.Embed(
            title=f"👛 Cartera de {target.display_name}",
            description=f"Tiene un saldo total de **{bal}** 🪙 Monedas Nexus.",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="diario", aliases=["daily"])
    async def diario(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.data:
            self.data[user_id] = {"coins": 500}

        self.data[user_id]["coins"] += 250
        self.guardar_datos()
        await ctx.send(f"🎁 {ctx.author.mention}, reclamaste tu recompensa diaria de **250** 🪙 Monedas Nexus.")

    @commands.command(name="comprar")
    async def comprar(self, ctx, rol_nombre: str):
        PRECIO_VIP = 1000
        ROL_VIP_NOMBRE = "VIP"

        user_id = str(ctx.author.id)
        bal = self.data.get(user_id, {}).get("coins", 500)

        if rol_nombre.lower() == "vip":
            if bal < PRECIO_VIP:
                await ctx.send(f"❌ No tienes suficientes monedas. El rol VIP cuesta `{PRECIO_VIP}` monedas.")
                return

            guild = ctx.guild
            rol = discord.utils.get(guild.roles, name=ROL_VIP_NOMBRE)
            if not rol:
                rol = await guild.create_role(name=ROL_VIP_NOMBRE, color=discord.Color.gold(), reason="Rol VIP de Economía")

            if user_id not in self.data:
                self.data[user_id] = {"coins": 500}

            self.data[user_id]["coins"] -= PRECIO_VIP
            self.guardar_datos()
            await ctx.author.add_roles(rol)
            await ctx.send(f"🎉 ¡Felicidades {ctx.author.mention}, compraste exitosamente el rol **VIP**!")
        else:
            await ctx.send("❌ Artículo no encontrado en la tienda. Usa `!comprar vip`.")

async def setup(bot):
    await bot.add_cog(SistemaEconomiaAvanzado(bot))