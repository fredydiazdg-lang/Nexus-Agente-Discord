import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import static_ffmpeg
import random
import aiohttp

static_ffmpeg.add_paths()

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'source_address': '0.0.0.0',
    'socket_timeout': 10,
    'retries': 2,
    'ignoreerrors': True,
    'nocheckcertificate': True,
    'no_warnings': True
}

if os.path.exists("cookies.txt"):
    YTDL_OPTIONS['cookiefile'] = "cookies.txt"

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 128k -bufsize 2048k'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

queues = {}          # Guild ID -> Lista de canciones pendientes
history = {}         # Guild ID -> Lista de canciones ya reproducidas
current = {}         # Guild ID -> Canción actual sonando
active_message = {}  # Guild ID -> Mensaje activo del player en Discord
volumes = {}         # Guild ID -> Nivel de volumen (0.0 a 2.0)
loop_single = {}     # Guild ID -> Bool (Repetir canción actual automáticamente)

TEXTO_FOOTER = "🎧 ¡Pídele una canción al DJ Nexus usando /play"

INSTANCIAS_INVIDIOUS = [
    "https://vid.puffyan.us",
    "https://invidious.nerdvpn.de",
    "https://inv.us.projectsegfau.lt",
    "https://invidious.epicsite.xyz"
]

async def obtener_stream_invidious(query):
    """Busca en instancias públicas de Invidious para evitar totalmente el bloqueo anti-bot de Render."""
    async with aiohttp.ClientSession() as session:
        for instancia in INSTANCIAS_INVIDIOUS:
            try:
                url_busqueda = f"{instancia}/api/v1/search?q={query}&type=video"
                async with session.get(url_busqueda, timeout=4) as resp:
                    if resp.status == 200:
                        resultados = await resp.json()
                        if resultados and len(resultados) > 0:
                            video_id = resultados[0].get('videoId')
                            titulo = resultados[0].get('title', 'Música')
                            thumbs = resultados[0].get('videoThumbnails', [])
                            thumb_url = thumbs[0].get('url') if thumbs else ''
                            
                            # Obtener streaming directo
                            url_info = f"{instancia}/api/v1/videos/{video_id}"
                            async with session.get(url_info, timeout=4) as resp_info:
                                if resp_info.status == 200:
                                    info_video = await resp_info.json()
                                    formatos = info_video.get('adaptiveFormats', [])
                                    # Filtrar solo stream de audio
                                    audio_formats = [f for f in formatos if 'audio' in f.get('type', '')]
                                    if audio_formats:
                                        # Tomar la mejor calidad de audio disponible
                                        audio_stream_url = audio_formats[0].get('url')
                                        return {
                                            'url_or_search': f"https://www.youtube.com/watch?v={video_id}",
                                            'url_stream': audio_stream_url,
                                            'title': titulo,
                                            'thumbnail': thumb_url
                                        }
            except Exception as e:
                print(f"Instancia {instancia} falló: {e}")
                continue
    return None

def reproducir_siguiente(vc, guild_id, bot):
    """Reproduce la siguiente canción utilizando el flujo de audio extraído."""
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
        url_stream = siguiente_track.get('url_stream')
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
            if siguiente_track.get('thumbnail'):
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

    @app_commands.command(name="play", description="Reproduce una canción o playlist")
    @app_commands.describe(busqueda="Nombre de la canción o enlace")
    async def play(self, interaction: discord.Interaction, busqueda: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Conéctate a un canal de voz primero.", ephemeral=True)
            return

        await interaction.response.defer()

        guild_id = interaction.guild_id
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            try:
                vc = await interaction.user.voice.channel.connect(timeout=10.0, reconnect=True, self_deaf=True)
            except Exception as e:
                print(f"Error conectando a voz: {e}")
                await interaction.followup.send("❌ No me pude conectar a tu canal de voz. Revisa los permisos.", ephemeral=True)
                return

        busqueda_limpia = busqueda.split("&si=")[0] if "&si=" in busqueda else busqueda

        try:
            # Extraer audio directamente saltando yt-dlp usando la API de Invidious
            cancion_nueva = await obtener_stream_invidious(busqueda_limpia)

            if not cancion_nueva:
                await interaction.followup.send("❌ No se encontraron resultados para esa búsqueda.", ephemeral=True)
                return

            titulo = cancion_nueva['title']
            thumbnail = cancion_nueva['thumbnail']

        except Exception as e:
            print(f"Error extracción audio: {e}")
            await interaction.followup.send("❌ Error procesando la canción.", ephemeral=True)
            return

        if guild_id not in queues:
            queues[guild_id] = []
        if guild_id not in history:
            history[guild_id] = []
        if guild_id not in volumes:
            volumes[guild_id] = 1.0

        queues[guild_id].append(cancion_nueva)

        if not vc.is_playing() and not vc.is_paused():
            reproducir_siguiente(vc, guild_id, self.bot)
            
            primer_track = current.get(guild_id, {'title': titulo, 'thumbnail': thumbnail})

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

        await interaction.followup.send(f"✅ Canción agregada a la cola: **{titulo}**", ephemeral=True)

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
