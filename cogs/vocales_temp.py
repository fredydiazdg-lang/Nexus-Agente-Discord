import discord
from discord.ext import commands

NOMBRE_CANAL_CREADOR = "🤜🤛· 𝐂𝐑𝐄𝐀𝐑 · 𝐒𝐀𝐋𝐀"

class VocalesTemp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.canales_creados = []

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 1. Cuando un usuario entra al canal creador
        if after.channel and after.channel.name == NOMBRE_CANAL_CREADOR:
            categoria = after.channel.category
            guild = member.guild
            
            # Crear canal temporal personalizado
            nuevo_canal = await guild.create_voice_channel(
                name=f"🔊 Sala de {member.display_name}",
                category=categoria
            )
            
            # Mover al usuario al nuevo canal
            await member.move_to(nuevo_canal)
            self.canales_creados.append(nuevo_canal.id)

        # 2. Cuando un usuario sale de una sala temporal y queda vacía
        if before.channel and before.channel.id in self.canales_creados:
            if len(before.channel.members) == 0:
                self.canales_creados.remove(before.channel.id)
                await before.channel.delete()

async def setup(bot):
    await bot.add_cog(VocalesTemp(bot))