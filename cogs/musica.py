import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import static_ffmpeg
import random

static_ffmpeg.add_paths()

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'socket_timeout': 30,
    'retries': 5,
    'extract_flat': 'in_playlist',
    'ignoreerrors': True,
    'nocheckcertificate': True,
    'no_warnings': True
}

YTDL_SINGLE_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'no_warnings': True
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32M -analyzeduration 0',
    'options': '-vn -b:a 192k -bufsize 1024k -ar 48000 -ac 2'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
ytdl_single = yt_dlp.YoutubeDL(YTDL_SINGLE_OPTIONS)

queues = {}          # Guild ID -> Lista de canciones pendientes
history = {}         # Guild ID -> Lista de canciones ya reproducidas
current = {}         # Guild ID -> Canción actual sonando
active_message = {}  # Guild ID -> Mensaje activo del player en Discord
volumes = {}         # Guild ID -> Nivel de volumen (0.0 a 2.0)
loop_single = {}     # Guild ID -> Bool (Repetir canción actual automáticamente)

TEXTO_FOOTER = "🎧 ¡Pídele una canción al DJ Nexus usando /play"

def reproducir_siguiente(vc, guild_id, bot):
    """Extrae la URL del flujo de audio directo de YouTube y reproduce la siguiente canción."""
    if loop_single.get(guild_id, False) and guild_id in current and current[guild_id]:
        siguiente_track = current[guild_id]
    elif guild_id in queues and len(queues[guild_id]) > 0:
        if guild_id in current and current[guild_id]:
            if guild_id not in history:
                history[guild_id] = []
            history[guild_id].append(current[guild_id])

        siguiente_track = queues[guild_id].pop(0)
    else:
        current[guild_id] = None
        return

    try:
        target = siguiente_track['url_or_search']
        if not target.startswith("http"):
            target = f"https://www.youtube.com/watch?v={target}"

        info_real = ytdl_single.extract_info(target, download=False)
        if 'entries' in info_real and len(info_real['entries']) > 0:
            info_real = info_real['entries'][0]

        url_stream = info_real.get('url')
        
        siguiente_track['title'] = info_real.get('title', siguiente_track['title'])
        siguiente_track['url_web'] = info_real.get('webpage_url', target)
        siguiente_track['thumbnail'] = info_real.get('thumbnail') or f"https://img.youtube.com/vi/{info_real.get('id')}/maxresdefault.jpg"
        current[guild_id] = siguiente_track

        if not url_stream:
            print("No se pudo obtener la URL del streaming de audio.")
            reproducir_siguiente(vc, guild_id, bot)
            return

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url_stream, **FFMPEG_OPTIONS))
        source.volume = volumes.get(guild_id, 1.0)
        vc.play(source, after=lambda e: reproducir_siguiente(vc, guild_id, bot))

        # Actualizar la tarjeta en Discord
        if guild_id in active_message and active_message[guild_id]:
            embed = discord.Embed(
                title="🎶 Now Playing",
                color=discord.Color.blue()
            )
            embed.add_field(name="Track:", value=f"`{siguiente_track['title']}`", inline=True)
            embed.add_field(name="Requested By:", value=f"{vc.guild.me.mention}", inline=True)
            vol_porcentaje = int(volumes.get(guild_id, 1.0) * 100)
            embed.add_field(name="Volumen:", value=f"`{vol_porcentaje}%`", inline=True)
            embed.set_image(url=siguiente_track['thumbnail'])
            embed.set_footer(text=TEXTO_FOOTER)

            bot.loop.create_task(active_message[guild_id].edit(embed=embed))

    except Exception as e:
        print(f"Error procesando pista: {e}")
        reproducir_siguiente(vc, guild_id, bot)


class VistaControlMusicaAzul(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    # FILA 0: Anterior, Pausa/Play, Siguiente
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.primary, row=0, custom_id="btn_prev")
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.defer()
            return

        if self.guild_id in history and len(history[self.guild_id]) > 0:
            cancion_previa = history[self.guild_id].pop()
            if self.guild_id in current and current[self.guild_id]:
                if self.guild_id not in queues:
                    queues[self.guild_id] = []
                queues[self.guild_id].insert(0, current[self.guild_id])

            queues[self.guild_id].insert(0, cancion_previa)
            await interaction.response.defer()
            vc.stop()
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0, custom_id="btn_play_pause")
    async def pausar_reanudar(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.defer()
            return

        if vc.is_playing():
            vc.pause()
        elif vc.is_paused():
            vc.resume()

        await interaction.response.defer()

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary, row=0, custom_id="btn_next")
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.defer()
            return

        await interaction.response.defer()
        if (self.guild_id in queues and len(queues[self.guild_id]) > 0) or vc.is_playing():
            vc.stop()

    # FILA 1: Silenciar (Mute), Bajar Volumen, Subir Volumen
    @discord.ui.button(emoji="🔇", style=discord.ButtonStyle.primary, row=1, custom_id="btn_mute")
    async def silenciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            vol_actual = volumes.get(self.guild_id, 1.0)
            if vol_actual > 0:
                volumes[f"{self.guild_id}_prev"] = vol_actual
                volumes[self.guild_id] = 0.0
                vc.source.volume = 0.0
            else:
                vol_previo = volumes.get(f"{self.guild_id}_prev", 1.0)
                volumes[self.guild_id] = vol_previo
                vc.source.volume = vol_previo

            if self.guild_id in active_message and active_message[self.guild_id] and self.guild_id in current:
                track = current[self.guild_id]
                embed = discord.Embed(title="🎶 Now Playing", color=discord.Color.blue())
                embed.add_field(name="Track:", value=f"`{track['title']}`", inline=True)
                embed.add_field(name="Requested By:", value=f"{vc.guild.me.mention}", inline=True)
                embed.add_field(name="Volumen:", value=f"`{int(volumes[self.guild_id] * 100)}%`", inline=True)
                if track.get('thumbnail'):
                    embed.set_image(url=track['thumbnail'])
                embed.set_footer(text=TEXTO_FOOTER)
                await active_message[self.guild_id].edit(embed=embed)

        await interaction.response.defer()

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.primary, row=1, custom_id="btn_voldown")
    async def bajar_vol(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            vol_actual = volumes.get(self.guild_id, 1.0)
            nuevo_vol = max(0.0, vol_actual - 0.2)
            volumes[self.guild_id] = nuevo_vol
            vc.source.volume = nuevo_vol

            if self.guild_id in active_message and active_message[self.guild_id] and self.guild_id in current:
                track = current[self.guild_id]
                embed = discord.Embed(title="🎶 Now Playing", color=discord.Color.blue())
                embed.add_field(name="Track:", value=f"`{track['title']}`", inline=True)
                embed.add_field(name="Requested By:", value=f"{vc.guild.me.mention}", inline=True)
                embed.add_field(name="Volumen:", value=f"`{int(nuevo_vol * 100)}%`", inline=True)
                if track.get('thumbnail'):
                    embed.set_image(url=track['thumbnail'])
                embed.set_footer(text=TEXTO_FOOTER)
                await active_message[self.guild_id].edit(embed=embed)

        await interaction.response.defer()

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.primary, row=1, custom_id="btn_volup")
    async def subir_vol(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            vol_actual = volumes.get(self.guild_id, 1.0)
            nuevo_vol = min(2.0, vol_actual + 0.2)
            volumes[self.guild_id] = nuevo_vol
            vc.source.volume = nuevo_vol

            if self.guild_id in active_message and active_message[self.guild_id] and self.guild_id in current:
                track = current[self.guild_id]
                embed = discord.Embed(title="🎶 Now Playing", color=discord.Color.blue())
                embed.add_field(name="Track:", value=f"`{track['title']}`", inline=True)
                embed.add_field(name="Requested By:", value=f"{vc.guild.me.mention}", inline=True)
                embed.add_field(name="Volumen:", value=f"`{int(nuevo_vol * 100)}%`", inline=True)
                if track.get('thumbnail'):
                    embed.set_image(url=track['thumbnail'])
                embed.set_footer(text=TEXTO_FOOTER)
                await active_message[self.guild_id].edit(embed=embed)

        await interaction.response.defer()

    # FILA 2: Ver Cola, Guardar en MP, Bucle automático continuo
    @discord.ui.button(emoji="📄", style=discord.ButtonStyle.primary, row=2, custom_id="btn_queue")
    async def ver_cola(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id not in queues or len(queues[self.guild_id]) == 0:
            await interaction.response.send_message("📜 La cola de reproducción está vacía.", ephemeral=True)
            return

        descripcion = ""
        for i, track in enumerate(queues[self.guild_id][:10], 1):
            descripcion += f"`{i}.` {track['title']}\n"

        if len(queues[self.guild_id]) > 10:
            descripcion += f"\n*... y {len(queues[self.guild_id]) - 10} canciones más.*"

        embed = discord.Embed(title="📜 Cola de Reproducción", description=descripcion, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji="💾", style=discord.ButtonStyle.primary, row=2, custom_id="btn_save")
    async def guardar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id in current and current[self.guild_id]:
            track = current[self.guild_id]
            try:
                embed = discord.Embed(
                    title="💾 Canción Guardada en tus Favoritos",
                    description=f"**Nombre:** [{track['title']}]({track.get('url_web', '#')})",
                    color=discord.Color.blue()
                )
                if track.get('thumbnail'):
                    embed.set_thumbnail(url=track['thumbnail'])
                await interaction.user.send(embed=embed)
            except:
                pass
        await interaction.response.defer()

    @discord.ui.button(emoji="♾️", style=discord.ButtonStyle.primary, row=2, custom_id="btn_infinite")
    async def infinito(self, interaction: discord.Interaction, button: discord.ui.Button):
        estado_actual = loop_single.get(self.guild_id, False)
        loop_single[self.guild_id] = not estado_actual
        await interaction.response.defer()

    # FILA 3: Reiniciar Canción Actual, Detener, Aleatorio
    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.primary, row=3, custom_id="btn_restart")
    async def reiniciar_cancion(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()) and self.guild_id in current and current[self.guild_id]:
            cancion_actual = current[self.guild_id]
            if self.guild_id not in queues:
                queues[self.guild_id] = []
            
            queues[self.guild_id].insert(0, cancion_actual)
            await interaction.response.defer()
            vc.stop()
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.primary, row=3, custom_id="btn_stop_all")
    async def detener(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if self.guild_id in queues:
            queues[self.guild_id].clear()
        if self.guild_id in history:
            history[self.guild_id].clear()
        current[self.guild_id] = None

        await interaction.response.defer()
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.primary, row=3, custom_id="btn_shuffle")
    async def aleatorio(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id in queues and len(queues[self.guild_id]) > 1:
            random.shuffle(queues[self.guild_id])
        await interaction.response.defer()


class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="Reproduce una canción o playlist de YouTube")
    @app_commands.describe(busqueda="Nombre de canción o link de playlist")
    async def play(self, interaction: discord.Interaction, busqueda: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Conéctate a un canal de voz primero.", ephemeral=True)
            return

        await interaction.response.defer()

        guild_id = interaction.guild_id
        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        busqueda_limpia = busqueda.split("&si=")[0] if "&si=" in busqueda else busqueda

        try:
            loop = asyncio.get_event_loop()
            search_query = busqueda_limpia if busqueda_limpia.startswith("http") else f"ytsearch:{busqueda_limpia}"
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            
            canciones_a_agregar = []

            if 'entries' in data and data['entries']:
                for entry in data['entries']:
                    if entry:
                        titulo = entry.get('title', 'Canción de Playlist')
                        url_video = entry.get('url') or entry.get('id')
                        canciones_a_agregar.append({
                            'url_or_search': url_video,
                            'title': titulo
                        })
                mensaje_info = f"🗂️ Se agregaron **{len(canciones_a_agregar)} canciones** a la cola."
            else:
                titulo = data.get('title', 'Canción de YouTube')
                url_video = data.get('webpage_url') or busqueda_limpia
                canciones_a_agregar.append({
                    'url_or_search': url_video,
                    'title': titulo
                })
                mensaje_info = f"🎶 Canción añadida a la cola."

        except Exception as e:
            await interaction.followup.send("❌ Error procesando el enlace o la búsqueda.", ephemeral=True)
            print(f"Error yt-dlp: {e}")
            return

        if guild_id not in queues:
            queues[guild_id] = []
        if guild_id not in history:
            history[guild_id] = []
        if guild_id not in volumes:
            volumes[guild_id] = 1.0

        queues[guild_id].extend(canciones_a_agregar)

        if not vc.is_playing() and not vc.is_paused():
            reproducir_siguiente(vc, guild_id, self.bot)
            
            primer_track = current.get(guild_id, {'title': 'Música', 'thumbnail': ''})

            embed = discord.Embed(
                title="🎶 Now Playing",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Track:", value=f"`{primer_track['title']}`", inline=True)
            embed.add_field(name="Requested By:", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="Volumen:", value=f"`{int(volumes[guild_id] * 100)}%`", inline=True)
            if primer_track.get('thumbnail'):
                embed.set_image(url=primer_track['thumbnail'])
            embed.set_footer(text=TEXTO_FOOTER)

            msg = await interaction.followup.send(embed=embed, view=VistaControlMusicaAzul(self.bot, guild_id))
            active_message[guild_id] = msg
            return

        await interaction.followup.send(f"✅ {mensaje_info} (Total en cola: {len(queues[guild_id])})", ephemeral=True)

    @app_commands.command(name="queue", description="Muestra las canciones en cola")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in queues or len(queues[guild_id]) == 0:
            await interaction.response.send_message("📜 La cola de reproducción está vacía.", ephemeral=True)
            return

        descripcion = ""
        for i, track in enumerate(queues[guild_id][:10], 1):
            descripcion += f"`{i}.` {track['title']}\n"

        if len(queues[guild_id]) > 10:
            descripcion += f"\n*... y {len(queues[guild_id]) - 10} canciones más.*"

        embed = discord.Embed(title="📜 Cola de Reproducción", description=descripcion, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Musica(bot))