import discord
from discord.ext import commands

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎮 Gamer", style=discord.ButtonStyle.primary, custom_id="rol_gamer")
    async def boton_gamer(self, interaction, button):
        await self.toggle_rol(interaction, "Gamer")

    @discord.ui.button(label="📢 Streamer", style=discord.ButtonStyle.success, custom_id="rol_streamer")
    async def boton_streamer(self, interaction, button):
        await self.toggle_rol(interaction, "Streamer")

    @discord.ui.button(label="⭐ VIP", style=discord.ButtonStyle.secondary, custom_id="rol_vip")
    async def boton_vip(self, interaction, button):
        await self.toggle_rol(interaction, "VIP")

    async def toggle_rol(self, interaction, nombre_rol):
        guild = interaction.guild
        rol = discord.utils.get(guild.roles, name=nombre_rol)
        if not rol:
            await interaction.response.send_message(f"❌ El rol **{nombre_rol}** no existe en el servidor.", ephemeral=True)
            return

        if rol in interaction.user.roles:
            await interaction.user.remove_roles(rol)
            await interaction.response.send_message(f"➖ Rol **{nombre_rol}** removido.", ephemeral=True)
        else:
            await interaction.user.add_roles(rol)
            await interaction.response.send_message(f"➕ Rol **{nombre_rol}** asignado.", ephemeral=True)

class Utilidad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        rol = discord.utils.get(member.guild.roles, name="Miembro")
        if rol:
            try:
                await member.add_roles(rol)
            except:
                pass

        canal = discord.utils.get(member.guild.text_channels, name="general")
        if canal:
            embed = discord.Embed(
                title="🎉 ¡Nuevo Miembro!",
                description=f"¡Bienvenido/a {member.mention}! NEXUS administra el servidor.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.name.lower() == "crear sala":
            cat = after.channel.category
            nuevo = await member.guild.create_voice_channel(
                name=f"🔊 Escuadra de {member.display_name}",
                category=cat
            )
            await member.move_to(nuevo)

        if before.channel and before.channel.name.startswith("🔊 Escuadra de"):
            if len(before.channel.members) == 0:
                await before.channel.delete()

    @commands.command(name="menu_roles")
    @commands.has_permissions(administrator=True)
    async def menu_roles(self, ctx):
        embed = discord.Embed(
            title="🎭 MENÚ DE ROLES AUTOMÁTICO",
            description="Haz clic en los botones para obtener tus roles:",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed, view=RoleView())

async def setup(bot):
    await bot.add_cog(Utilidad(bot))