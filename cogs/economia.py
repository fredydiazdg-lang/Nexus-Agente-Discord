import discord
from discord.ext import commands
import random

# Base de datos simulada o ligada
user_balance = {}

def get_balance(user_id):
    if user_id not in user_balance:
        user_balance[user_id] = 500
    return user_balance[user_id]

def update_balance(user_id, amount):
    user_balance[user_id] = get_balance(user_id) + amount

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trabajar", aliases=["work"])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def trabajar(self, ctx):
        ganancia = random.randint(100, 350)
        update_balance(ctx.author.id, ganancia)

        trabajos = [
            f"Completaste una partida clasificatoria de Free Fire y ganaste **{ganancia}** 🪙 Monedas.",
            f"Ayudaste a administrar el servidor de Discord y recibiste **{ganancia}** 🪙 Monedas.",
            f"Ganaste un torneo de escuadras y cobraste **{ganancia}** 🪙 Monedas."
        ]
        await ctx.send(f"💼 {ctx.author.mention} {random.choice(trabajos)}")

    @trabajar.error
    async def trabajar_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutos = int(error.retry_after // 60)
            await ctx.send(f"⏳ {ctx.author.mention}, estás cansado. Vuelve a trabajar en **{minutos} minutos**.")

    @commands.command(name="ruleta", aliases=["apostar"])
    async def ruleta(self, ctx, cantidad: int, color: str):
        color = color.lower()
        if color not in ["rojo", "negro", "verde"]:
            await ctx.send("❌ Elige un color válido: `rojo`, `negro` o `verde` (ejemplo: `!ruleta 100 rojo`).")
            return

        saldo = get_balance(ctx.author.id)
        if cantidad <= 0 or cantidad > saldo:
            await ctx.send(f"❌ No tienes suficientes monedas. Saldo actual: **{saldo}** 🪙.")
            return

        resultado_num = random.randint(0, 36)
        if resultado_num == 0:
            resultado_color = "verde"
        elif resultado_num % 2 == 0:
            resultado_color = "rojo"
        else:
            resultado_color = "negro"

        if color == resultado_color:
            multiplicador = 14 if color == "verde" else 2
            ganancia = cantidad * multiplicador
            update_balance(ctx.author.id, ganancia - cantidad)
            await ctx.send(f"🎰 ¡La ruleta cayó en **{resultado_color.upper()} ({resultado_num})**! 🎉 {ctx.author.mention} ganaste **{ganancia}** 🪙 Monedas.")
        else:
            update_balance(ctx.author.id, -cantidad)
            await ctx.send(f"🎰 La ruleta cayó en **{resultado_color.upper()} ({resultado_num})**. ❌ {ctx.author.mention} perdiste **{cantidad}** 🪙 Monedas.")

    @commands.command(name="robar", aliases=["rob"])
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def robar(self, ctx, victima: discord.Member):
        if victima.id == ctx.author.id:
            await ctx.send("❌ No te puedes robar a ti mismo.")
            return

        saldo_victima = get_balance(victima.id)
        if saldo_victima < 100:
            await ctx.send(f"❌ {victima.display_name} es demasiado pobre para robarle.")
            return

        exito = random.choice([True, False])
        if exito:
            monto = random.randint(50, int(saldo_victima * 0.4))
            update_balance(victima.id, -monto)
            update_balance(ctx.author.id, monto)
            await ctx.send(f"🥷 ¡{ctx.author.mention} le robó **{monto}** 🪙 Monedas a {victima.mention}!")
        else:
            multa = random.randint(50, 150)
            update_balance(ctx.author.id, -multa)
            await ctx.send(f"🚨 ¡Atraparon a {ctx.author.mention} intentando robar y pagó una multa de **{multa}** 🪙 Monedas!")

    @robar.error
    async def robar_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutos = int(error.retry_after // 60)
            await ctx.send(f"⏳ {ctx.author.mention}, la policía te busca. Espera **{minutos} minutos** antes de volver a robar.")

async def setup(bot):
    await bot.add_cog(Economia(bot))