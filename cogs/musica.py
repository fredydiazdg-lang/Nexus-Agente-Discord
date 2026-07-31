import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import random

TEXTO_FOOTER = "🎧 ¡Pídele una canción al DJ Nexus usando /play"

class VistaControlLavalink(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.primary, row=0, custom_id="lav_prev")
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0, custom_id="lav_pause")
    async def pausar_reanudar(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            await player.pause(not player.paused)
        await interaction.response.defer()

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary, row=0, custom_id="lav_next")
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            if not player.queue.is_empty:
                await player.skip(force=True)
            else:
                await player.stop()
        await interaction.response.defer()

    @discord.ui.button(emoji="🔇", style=discord.ButtonStyle.primary, row=1, custom_id="lav_mute")
    async def silenciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            current_vol = player.volume
            if current_vol > 0:
                self.prev_vol = current_vol
                await player.set_volume(0)
            else:
                await player.set_volume(getattr(self, 'prev_vol', 100))
        await interaction.response.defer()

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.primary, row=1, custom_id="lav_voldown")
    async def bajar_vol(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            nuevo_vol = max(0, player.volume - 20)
            await player.set_volume(nuevo_vol)
        await interaction.response.defer()

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.primary, row=1, custom_id="lav_volup")
    async def subir_vol(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            nuevo_vol = min(150, player.volume + 20)
            await player.set_volume(nuevo_vol)
        await interaction.response.defer()

    @discord.ui.button(emoji="📄", style=discord.ButtonStyle.primary, row=2, custom_id="lav_queue")
    async def ver_cola(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if not player or player.queue.is_empty:
            await interaction.response.send_message("📜 La cola de reproducción está vacía.", ephemeral=True)
            return

        descripcion = ""
        for i, track in enumerate(list(player.queue)[:10], 1):
            descripcion += f"`{i}.` {track.title}\n"

        embed = discord.Embed(title="📜 Cola de Reproducción", description=descripcion, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji="💾", style=discord.ButtonStyle.primary, row=2, custom_id="lav_save")
    async def guardar(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player and player.current:
            try:
                embed = discord.Embed(
                    title="💾 Canción Guardada en tus Favoritos",
                    description=f"**Nombre:** [{player.current.title}]({player.current.uri})",
                    color=discord.Color.blue()
                )
                if hasattr(player.current, 'artwork') and player.current.artwork:
                    embed.set_thumbnail(url=player.current.artwork)
                await interaction.user.send(embed=embed)
            except:
                pass
        await interaction.response.defer()

    @discord.ui.button(emoji="♾️", style=discord.ButtonStyle.primary, row=2, custom_id="lav_loop")
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            if player.queue.mode == wavelink.QueueMode.normal:
                player.queue.mode = wavelink.QueueMode.loop
                await interaction.response.send_message("🔁 Bucle de pista activado.", ephemeral=True)
            else:
                player.queue.mode = wavelink.QueueMode.normal
                await interaction.response.send_message("➡️ Bucle desactivado.", ephemeral=True)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.primary, row=3, custom_id="lav_stop")
    async def detener(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            player.queue.clear()
            await player.disconnect()
        await interaction.response.defer()

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.primary, row=3, custom_id="lav_shuffle")
    async def aleatorio(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player and len(player.queue) > 1:
            player.queue.shuffle()
        await interaction.response.defer()


class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.conectar_lavalink())

    async def conectar_lavalink(self):
        await self.bot.wait_until_ready()
        nodos = [
            wavelink.Node(uri="https://lavalink.vcodes.xyz:443", password="youshallnotpass"),
            wavelink.Node(uri="https://lava-v3.ajiehospitality.sh:443", password="youwillnotpass")
        ]
        for node in nodos:
            try:
                await wavelink.Pool.connect(nodes=[node], client=self.bot)
                print(f"✅ Conectado al nodo Lavalink: {node.uri}")
                break
            except Exception as e:
                print(f"⚠️ Falló nodo {node.uri}: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player: wavelink.Player = payload.player
        if not player:
            return
        if not player.queue.is_empty:
            siguiente = await player.queue.get_wait()
            await player.play(siguiente)

    @app_commands.command(name="play", description="Reproduce una canción o playlist sin bloqueos")
    @app_commands.describe(busqueda="Nombre de la canción o enlace")
    async def play(self, interaction: discord.Interaction, busqueda: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Conéctate a un canal de voz primero.", ephemeral=True)
            return

        await interaction.response.defer()

        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
            except Exception as e:
                print(f"Error conectando a voz: {e}")
                await interaction.followup.send("❌ No me pude conectar a tu canal de voz.", ephemeral=True)
                return

        # Búsqueda universal por Lavalink (soporta YouTube, Spotify, etc.)
        tracks: wavelink.Search = await wavelink.Playable.search(busqueda)
        if not tracks:
            await interaction.followup.send("❌ No se encontraron resultados.", ephemeral=True)
            return

        if isinstance(tracks, wavelink.Search):
            track = tracks[0]
        else:
            track = tracks.tracks[0]

        if player.is_playing():
            await player.queue.put_wait(track)
            await interaction.followup.send(f"✅ Canción agregada a la cola: **{track.title}**", ephemeral=True)
        else:
            await player.play(track)
            embed = discord.Embed(title="🎶 Now Playing", color=discord.Color.blue())
            embed.add_field(name="Track:", value=f"`{track.title}`", inline=True)
            embed.add_field(name="Requested By:", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="Volumen:", value="`100%`", inline=True)
            if hasattr(track, 'artwork') and track.artwork:
                embed.set_image(url=track.artwork)
            embed.set_footer(text=TEXTO_FOOTER)

            await interaction.followup.send(embed=embed, view=VistaControlLavalink())

    @app_commands.command(name="queue", description="Muestra las canciones en cola")
    async def queue(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        if not player or player.queue.is_empty:
            await interaction.response.send_message("📜 La cola de reproducción está vacía.", ephemeral=True)
            return

        descripcion = ""
        for i, track in enumerate(list(player.queue)[:10], 1):
            descripcion += f"`{i}.` {track.title}\n"

        embed = discord.Embed(title="📜 Cola de Reproducción", description=descripcion, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Musica(bot))
