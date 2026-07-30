import discord
from discord.ext import commands

user_xp = {}

def add_xp(user_id, amount=15):
    if user_id not in user_xp:
        user_xp[user_id] = {"xp": 0, "nivel": 1}
    
    user_xp[user_id]["xp"] += amount
    xp_necesaria = user_xp[user_id]["nivel"] * 100
    
    if user_xp[user_id]["xp"] >= xp_necesaria:
        user_xp[user_id]["nivel"] += 1
        return user_xp[user_id]["nivel"]
    return None

class Niveles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content.startswith("!"):
            return

        nuevo_lvl = add_xp(message.author.id)
        if nuevo_lvl:
            embed = discord.Embed(
                title="🌟 ¡Nivel Aumentado!",
                description=f"¡Felicidades {message.author.mention}! Has subido al **Nivel {nuevo_lvl}**.",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed, delete_after=6)

    @commands.command(name="rank", aliases=["nivel"])
    async def rank(self, ctx, miembro: discord.Member = None):
        target = miembro or ctx.author
        data = user_xp.get(target.id, {"xp": 0, "nivel": 1})
        
        embed = discord.Embed(
            title=f"📊 Rango de {target.display_name}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Nivel", value=f"⭐ **{data['nivel']}**", inline=True)
        embed.add_field(name="Puntos XP", value=f"⚡ **{data['xp']} XP**", inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Niveles(bot))