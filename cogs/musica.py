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

# Opciones optimizadas de yt-dlp para Render
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'source_address': '0.0.0.0',
    'socket_timeout': 10,
    'retries': 2,
    'ignoreerrors': True,
    'nocheckcertificate': True,
    'no_warnings': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['mweb', 'android']
        }
    }
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

async def buscar_video_api(query):
    """Busca en la API pública de Piped/Invidious para saltarse el bloqueo de IP de Render."""
    apis = [
        f"https://pipedapi.kavin.rocks/search?q={query}&filter=videos",
        f"https://api.invidious.io/api/v1/search?q={query}&type=video"
    ]
    
    async with aiohttp.ClientSession() as session:
        for api_url in apis:
            try:
                async with session.get(api_url, timeout=4) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get('items', []) if 'items' in data else data
                        for item in items:
                            v_id = item.get('url', '').replace('/watch?v=', '') or item.get('videoId')
                            if v_id:
                                return f"https://www.youtube.com/watch?v={v_id}"
            except Exception as e:
                print(f"Error consultando API alternativa: {e}")
    return None

def obtener_info_busqueda(query):
    """Intenta extracción directa si es un enlace de YouTube o SoundCloud."""
    if query.startswith("http"):
        return ytdl.extract_info(query, download=False)
    
    # Intento con ytsearch estándar por si Render lo deja pasar
    try:
        data = ytdl.extract_info(f"ytsearch:{query}", download=False)
        if data and 'entries' in data and len(data['entries']) > 0 and data['entries'][0]:
            return data
    except Exception as e:
        print(f"Búsqueda directa falló: {e}")
        
    return None

def reproducir_siguiente(vc, guild_id, bot):
    """Extrae la URL del flujo de audio directo y reproduce la siguiente canción."""
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
        
        if not url_stream:
            target = siguiente_track['url_or_search']
            info = ytdl.extract_info(target, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]
            url_stream = info.get('url')
            siguiente_track['title'] = info.get('title', siguiente_track['title'])
            siguiente_track['thumbnail'] = info.get('thumbnail', '')

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
            # 1. Intentar la extracción directa con yt-dlp
            data = await asyncio.to_thread(obtener_info_busqueda, busqueda_limpia)
            
            # 2. Si falla por el bloqueo anti-bot de Render, buscar la URL real con la API externa
            if not data and not busqueda_limpia.startswith("http"):
                url_directa = await buscar_video_api(busqueda_limpia)
                if url_directa:
                    data = await asyncio.to_thread(ytdl.extract_info, url_directa, download=False)

            if not data:
                await interaction.followup.send("❌ No se encontraron resultados para esa búsqueda.", ephemeral=True)
                return

            if 'entries' in data and data['entries']:
                entry = data['entries'][0]
            else:
                entry = data

            titulo = entry.get('title', 'Canción en reproducción')
            url_stream = entry.get('url')
            url_web = entry.get('webpage_url', busqueda_limpia)
            thumbnail = entry.get('thumbnail', '')

            cancion_nueva = {
                'url_or_search': url_web,
                'url_stream': url_stream,
                'title': titulo,
                'thumbnail': thumbnail
            }

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
