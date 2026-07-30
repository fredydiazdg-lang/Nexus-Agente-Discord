import discord
from discord.ext import commands, tasks
import aiohttp
import json

# ⚙️ CONFIGURACIÓN DE TU CANAL Y TIKTOK
ID_CANAL_DIRECTOS = 1479517194932195522
USUARIO_TIKTOK = "maestro_freefire_"
LINK_TIKTOK = f"https://www.tiktok.com/@{USUARIO_TIKTOK}/live"

class NotificadorLiveAuto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.en_vivo = False  # Controla si ya se envió la alerta para no hacer spam
        self.comprobar_directo.start()  # Inicia la revisión automática

    def cog_unload(self):
        self.comprobar_directo.cancel()

    @tasks.loop(minutes=2)  # Revisa cada 2 minutos
    async def comprobar_directo(self):
        await self.bot.wait_until_ready()
        
        canal = self.bot.get_channel(ID_CANAL_DIRECTOS)
        if not canal:
            return

        # Consulta el estado público de tu TikTok
        url_api = f"https://www.tiktok.com/api/live/detail/?aid=1988&roomID=&uniqueId={USUARIO_TIKTOK}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url_api, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verifica el estado del Live de TikTok
                        status = data.get("LiveRoomInfo", {}).get("status", 0)

                        # Status 2 significa que la transmisión está EN VIVO
                        if status == 2 and not self.en_vivo:
                            self.en_vivo = True
                            
                            embed = discord.Embed(
                                title="🔴 ¡ESTAMOS EN DIRECTO EN TIKTOK!",
                                description=(
                                    f"🔥 ¡Transmisión en vivo iniciada!\n\n"
                                    f"🚀 Entra a apoyar el stream de Free Fire aquí:\n"
                                    f"👉 **[HAZ CLIC AQUÍ PARA ENTRAR AL LIVE]({LINK_TIKTOK})**"
                                ),
                                color=discord.Color.from_rgb(255, 0, 80)
                            )
                            if canal.guild.icon:
                                embed.set_thumbnail(url=canal.guild.icon.url)
                            embed.set_footer(text="NEXUS Automatic TikTok Detection")

                            await canal.send(content="🚨 @everyone ¡Atención comunidad, ya encendimos Stream en TikTok! 🚨", embed=embed)

                        elif status != 2 and self.en_vivo:
                            # Se apagó el directo, reseteamos el estado
                            self.en_vivo = False

        except Exception as e:
            pass  # Evita errores en la consola si TikTok no responde

async def setup(bot):
    await bot.add_cog(NotificadorLiveAuto(bot))