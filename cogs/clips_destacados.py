import discord
from discord.ext import commands

# Nombre exacto de tu canal de clips
NOMBRE_CANAL_CLIPS = "clips-comunidad"

class VotacionClipView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.votos_god = set()
        self.votos_headshot = set()
        self.votos_f = set()

    @discord.ui.button(label="🔥 GOD (0)", style=discord.ButtonStyle.danger, custom_id="btn_god_clip")
    async def voto_god(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.votos_god:
            self.votos_god.remove(user_id)
        else:
            self.votos_god.add(user_id)

        button.label = f"🔥 GOD ({len(self.votos_god)})"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="🎯 Headshot (0)", style=discord.ButtonStyle.primary, custom_id="btn_headshot_clip")
    async def voto_headshot(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.votos_headshot:
            self.votos_headshot.remove(user_id)
        else:
            self.votos_headshot.add(user_id)

        button.label = f"🎯 Headshot ({len(self.votos_headshot)})"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="💩 F (0)", style=discord.ButtonStyle.secondary, custom_id="btn_f_clip")
    async def voto_f(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.votos_f:
            self.votos_f.remove(user_id)
        else:
            self.votos_f.add(user_id)

        button.label = f"💩 F ({len(self.votos_f)})"
        await interaction.response.edit_message(view=self)

class ClipsDestacados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Verificar si el mensaje fue enviado en el canal de clips
        if NOMBRE_CANAL_CLIPS in message.channel.name.lower():
            # Si contiene un archivo/video adjunto o un enlace (TikTok, YouTube, etc.)
            if message.attachments or "http://" in message.content or "https://" in message.content:
                view = VotacionClipView()
                await message.reply("👇 **¡Vota por este clip de la comunidad!**", view=view)

async def setup(bot):
    await bot.add_cog(ClipsDestacados(bot))