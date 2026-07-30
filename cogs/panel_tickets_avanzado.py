import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime

# ID de la categoría donde se organizan los tickets
ID_CATEGORIA_TICKETS = 1520372482216034444

# 📌 PEGA AQUÍ EL ID DE TU CANAL #historial-tickets
ID_CANAL_HISTORIAL = 1532137453626855664  # <--- REEMPLAZA CON TU ID REAL

# Imagen del Panel Principal
URL_IMAGEN_PANEL = "https://i.postimg.cc/tT4NtDBM/Chat-GPT-Image-27-jun-2026-16-38-32.png"

ARCHIVO_CONTADOR = "contador_tickets.json"
ARCHIVO_HISTORIAL = "historial_tickets_db.json"

def formatear_fecha_corta(dt_obj):
    if not dt_obj:
        return "N/A"
    return dt_obj.strftime("%d/%m %H:%M")

def obtener_siguiente_numero():
    contador = 1
    if os.path.exists(ARCHIVO_CONTADOR):
        try:
            with open(ARCHIVO_CONTADOR, "r") as f:
                datos = json.load(f)
                contador = datos.get("numero", 1)
        except Exception:
            contador = 1

    with open(ARCHIVO_CONTADOR, "w") as f:
        json.dump({"numero": contador + 1}, f)

    return str(contador).zfill(4)

def guardar_registro_historial(ticket_nombre, tema, estado, horario_abierto, horario_resuelto, autor):
    historial = []
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = []

    encontrado = False
    for item in historial:
        if item["ticket"] == ticket_nombre:
            item["estado"] = estado
            item["resuelto"] = horario_resuelto
            encontrado = True
            break

    if not encontrado:
        historial.insert(0, {
            "ticket": ticket_nombre,
            "tema": tema,
            "estado": estado,
            "abierto": horario_abierto,
            "resuelto": horario_resuelto,
            "autor": autor
        })

    historial = historial[:10]

    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

    return historial

async def actualizar_canal_historial(guild):
    try:
        canal_historial = guild.get_channel(ID_CANAL_HISTORIAL) or discord.utils.get(guild.text_channels, name="historial-tickets")
        if not canal_historial:
            print("⚠️ No se encontró el canal de historial.")
            return

        historial = []
        if os.path.exists(ARCHIVO_HISTORIAL):
            try:
                with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                    historial = json.load(f)
            except Exception:
                historial = []

        col_1 = "BILLETE".ljust(13)
        col_2 = "TEMA".ljust(22)
        col_3 = "ESTADO".ljust(13)
        col_4 = "ABIERTO".ljust(13)
        col_5 = "RESUELTO".ljust(13)
        col_6 = "AUTOR\n"

        encabezado = col_1 + col_2 + col_3 + col_4 + col_5 + col_6
        separador = "=" * 85 + "\n"

        contenido_tabla = ""
        if not historial:
            contenido_tabla = "Sin registros recientes de entradas.\n"
        else:
            for item in historial:
                ticket = item['ticket'].ljust(13)
                tema = item['tema'][:20].ljust(22)
                estado = item['estado'][:12].ljust(13)
                abierto = item['abierto'].ljust(13)
                resuelto = item['resuelto'].ljust(13)
                autor = item['autor'][:12]

                contenido_tabla += f"{ticket}{tema}{estado}{abierto}{resuelto}{autor}\n"

        embed = discord.Embed(
            title="📋 HISTORIAL RECIENTE DE BILLETES",
            description=f"```txt\n{encabezado}{separador}{contenido_tabla}```",
            color=discord.Color.dark_grey()
        )
        embed.set_footer(text="NEXUS Ticket System • Live Dashboard")

        mensaje_encontrado = None
        async for msg in canal_historial.history(limit=30):
            if msg.author == guild.me and msg.embeds:
                if "HISTORIAL RECIENTE DE BILLETES" in msg.embeds[0].title:
                    mensaje_encontrado = msg
                    break

        if mensaje_encontrado:
            await mensaje_encontrado.edit(embed=embed)
        else:
            await canal_historial.send(embed=embed)

    except Exception as e:
        print(f"Error actualizando historial: {e}")


class VistaGestionTicket(discord.ui.View):
    def __init__(self, tipo_ticket: str, fecha_apertura: str, nombre_canal: str, autor_nombre: str):
        super().__init__(timeout=None)
        self.tipo_ticket = tipo_ticket
        self.fecha_apertura = fecha_apertura
        self.nombre_canal = nombre_canal
        self.autor_nombre = autor_nombre

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="btn_close_ticket_pro")
    async def cerrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **Cerrando ticket y actualizando registro...**")

        canal = interaction.channel
        fecha_cierre = formatear_fecha_corta(datetime.now())
        mensajes = []
        
        async for msg in canal.history(limit=500, oldest_first=True):
            fecha_msg = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            mensajes.append(f"[{fecha_msg}] {msg.author.name}: {msg.content}")

        texto_transcripcion = "\n".join(mensajes)
        nombre_archivo = f"transcripcion-{canal.name}.txt"
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(f"=== HISTORIAL DE TICKET: {canal.name} ===\n\n")
            f.write(texto_transcripcion)

        guardar_registro_historial(
            ticket_nombre=self.nombre_canal,
            tema=self.tipo_ticket,
            estado="Resuelto",
            horario_abierto=self.fecha_apertura,
            horario_resuelto=fecha_cierre,
            autor=self.autor_nombre
        )
        await actualizar_canal_historial(interaction.guild)

        canal_logs = discord.utils.get(interaction.guild.text_channels, name="logs") or discord.utils.get(interaction.guild.text_channels, name="staff_logs")
        if canal_logs:
            embed_log = discord.Embed(
                title=f"📄 Transcripción Guardada: {canal.name}",
                description=f"Cerrado por {interaction.user.mention}",
                color=discord.Color.red()
            )
            await canal_logs.send(embed=embed_log, file=discord.File(nombre_archivo))

        if os.path.exists(nombre_archivo):
            os.remove(nombre_archivo)

        await asyncio.sleep(1)
        await canal.delete()

    @discord.ui.button(label="Claim Ticket", emoji="📌", style=discord.ButtonStyle.secondary, custom_id="btn_claim_ticket_pro")
    async def reclamar(self, interaction: discord.Interaction, button: discord.ui.Button):
        guardar_registro_historial(
            ticket_nombre=self.nombre_canal,
            tema=self.tipo_ticket,
            estado="En progreso",
            horario_abierto=self.fecha_apertura,
            horario_resuelto="N/A",
            autor=self.autor_nombre
        )
        await actualizar_canal_historial(interaction.guild)

        embed_claim = discord.Embed(
            title="Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed_claim)


class VistaPanelPrincipalTickets(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def crear_canal_ticket(self, interaction: discord.Interaction, tipo_ticket: str):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        categoria = guild.get_channel(ID_CATEGORIA_TICKETS)

        num_ticket = obtener_siguiente_numero()
        nombre_canal = f"ticket-{num_ticket}"
        fecha_apertura = formatear_fecha_corta(datetime.now())

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        rol_staff = discord.utils.get(guild.roles, name="staff") or discord.utils.get(guild.roles, name="Staff")
        if rol_staff:
            overwrites[rol_staff] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            canal_creado = await guild.create_text_channel(
                name=nombre_canal,
                category=categoria if isinstance(categoria, discord.CategoryChannel) else None,
                overwrites=overwrites
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error al crear el canal: {e}", ephemeral=True)
            return

        embed_bienvenida = discord.Embed(
            title="Ticket Opened",
            description=f"{interaction.user.mention} has created a new **{tipo_ticket}** ticket.",
            color=discord.Color.gold()
        )
        embed_bienvenida.set_footer(text="NEXUS Ticket System")
        
        await canal_creado.send(
            content=f"{interaction.user.mention}", 
            embed=embed_bienvenida, 
            view=VistaGestionTicket(
                tipo_ticket=tipo_ticket, 
                fecha_apertura=fecha_apertura, 
                nombre_canal=nombre_canal,
                autor_nombre=interaction.user.name
            )
        )

        await interaction.followup.send(f"✅ ¡Tu ticket ha sido creado correctamente! Entra aquí: {canal_creado.mention}", ephemeral=True)

        guardar_registro_historial(
            ticket_nombre=nombre_canal,
            tema=tipo_ticket,
            estado="En curso",
            horario_abierto=fecha_apertura,
            horario_resuelto="N/A",
            autor=interaction.user.name
        )
        await actualizar_canal_historial(guild)

    @discord.ui.button(label="🎟️ QUIERO COMPRAR PANEL", style=discord.ButtonStyle.primary, custom_id="btn_ticket_comprar_panel")
    async def ticket_comprar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.crear_canal_ticket(interaction, "QUIERO COMPRAR PANEL")

    @discord.ui.button(label="🎟️ SOPORTE", style=discord.ButtonStyle.danger, custom_id="btn_ticket_soporte")
    async def ticket_soporte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.crear_canal_ticket(interaction, "SOPORTE")

    @discord.ui.button(label="🎟️ QUIERO ABLAR DE OTRO TEMA", style=discord.ButtonStyle.success, custom_id="btn_ticket_otro")
    async def ticket_otro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.crear_canal_ticket(interaction, "QUIERO ABLAR DE OTRO TEMA")


class PanelTicketsAvanzado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(2)
        for guild in self.bot.guilds:
            await actualizar_canal_historial(guild)

    @commands.command(name="panelticket")
    @commands.has_permissions(administrator=True)
    async def desplegar_panel(self, ctx):
        await ctx.message.delete()

        embed = discord.Embed(
            title="Help & Support",
            description=(
                "que tal herman@ soy maestriño en la parte de arriba a la izaquierda "
                "de discord esta tu ticket ingresa ahi donde podre darte acceso acualquier "
                "producto que quieras y ablar de precios 🎟️"
            ),
            color=discord.Color.gold()
        )
        if URL_IMAGEN_PANEL:
            embed.set_image(url=URL_IMAGEN_PANEL)

        embed.set_footer(text="Powered by NEXUS System")

        await ctx.send(
            content="**BIENVENIDOS AL MEJOR SERVIDOR DE LATAM TENGO LOS MEJORES PANELES PARA CU EN TU DIA DE COMPRAS**",
            embed=embed,
            view=VistaPanelPrincipalTickets()
        )

async def setup(bot):
    await bot.add_cog(PanelTicketsAvanzado(bot))