import discord
from discord.ext import commands

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Abrir Ticket de Soporte", style=discord.ButtonStyle.success, custom_id="abrir_ticket")
    async def crear_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        categoria = discord.utils.get(guild.categories, name="TICKETS")
        
        if not categoria:
            categoria = await guild.create_category("TICKETS")

        # Permisos del canal privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        canal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites
        )
        await interaction.response.send_message(f"✅ Tu ticket ha sido creado en {canal.mention}", ephemeral=True)
        await canal.send(f"👋 Hola {interaction.user.mention}, describe tu problema y un administrador te atenderá pronto.")

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel_tickets")
    @commands.has_permissions(administrator=True)
    async def panel_tickets(self, ctx):
        embed = discord.Embed(
            title="🎫 SISTEMA DE SOPORTE Y AYUDA",
            description="¿Necesitas hablar con el staff o resolver una duda? Haz clic abajo para abrir un ticket privado.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketView())

async def setup(bot):
    await bot.add_cog(Tickets(bot))