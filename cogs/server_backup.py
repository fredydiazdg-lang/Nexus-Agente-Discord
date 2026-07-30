import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class ServerBackup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_dir = "backups"
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    backup_group = app_commands.Group(name="backup", description="Sistema de copias de seguridad del servidor")

    @backup_group.command(name="crear", description="Crea una copia de seguridad completa de la estructura del servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_crear(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        guild = interaction.guild

        try:
            data = {
                "server_name": guild.name,
                "roles": [],
                "categories": [],
                "channels": []
            }

            # 1. Respaldar Roles (excluyendo @everyone y roles integrados de bots)
            for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
                if role.is_default() or role.managed:
                    continue
                data["roles"].append({
                    "name": role.name,
                    "color": role.color.value,
                    "permissions": role.permissions.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "position": role.position
                })

            # 2. Respaldar Categorías y Canales
            for category in guild.categories:
                cat_data = {
                    "name": category.name,
                    "position": category.position,
                    "channels": []
                }
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        cat_data["channels"].append({
                            "type": "text",
                            "name": channel.name,
                            "topic": channel.topic,
                            "slowmode": channel.slowmode_delay,
                            "nsfw": channel.nsfw,
                            "position": channel.position
                        })
                    elif isinstance(channel, discord.VoiceChannel):
                        cat_data["channels"].append({
                            "type": "voice",
                            "name": channel.name,
                            "bitrate": channel.bitrate,
                            "user_limit": channel.user_limit,
                            "position": channel.position
                        })
                data["categories"].append(cat_data)

            # Canales sin categoría (fuera de categoría)
            uncategorized = []
            for channel in guild.channels:
                if channel.category is None and not isinstance(channel, discord.ForumChannel):
                    if isinstance(channel, discord.TextChannel):
                        uncategorized.append({
                            "type": "text",
                            "name": channel.name,
                            "topic": channel.topic,
                            "position": channel.position
                        })
                    elif isinstance(channel, discord.VoiceChannel):
                        uncategorized.append({
                            "type": "voice",
                            "name": channel.name,
                            "position": channel.position
                        })
            data["uncategorized_channels"] = uncategorized

            # Guardar en archivo JSON único por servidor
            file_path = os.path.join(self.backup_dir, f"backup_{guild.id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            embed = discord.Embed(
                title="🛡️ Copia de Seguridad Creada con Éxito",
                description=f"Se ha respaldado la estructura de **{guild.name}** correctamente.\nRoles guardados: `{len(data['roles'])}`\nCategorías: `{len(data['categories'])}`",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error al crear el respaldo: {e}", ephemeral=True)

    @backup_group.command(name="restaurar", description="Restaura roles y canales básicos desde el último respaldo guardado")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_restaurar(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        file_path = os.path.join(self.backup_dir, f"backup_{guild.id}.json")

        if not os.path.exists(file_path):
            await interaction.followup.send("❌ No se encontró ninguna copia de seguridad guardada para este servidor.", ephemeral=True)
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Restaurar Roles
            for r_data in data.get("roles", []):
                existing_role = discord.utils.get(guild.roles, name=r_data["name"])
                if not existing_role:
                    await guild.create_role(
                        name=r_data["name"],
                        color=discord.Color(r_data["color"]),
                        permissions=discord.Permissions(r_data["permissions"]),
                        hoist=r_data["hoist"],
                        mentionable=r_data["mentionable"]
                    )

            # Restaurar Categorías y Canales
            for cat_data in data.get("categories", []):
                existing_cat = discord.utils.get(guild.categories, name=cat_data["name"])
                if not existing_cat:
                    existing_cat = await guild.create_category(name=cat_data["name"])

                for ch_data in cat_data.get("channels", []):
                    existing_ch = discord.utils.get(existing_cat.channels, name=ch_data["name"])
                    if not existing_ch:
                        if ch_data["type"] == "text":
                            await guild.create_text_channel(
                                name=ch_data["name"],
                                category=existing_cat,
                                topic=ch_data.get("topic"),
                                slowmode_delay=ch_data.get("slowmode", 0),
                                nsfw=ch_data.get("nsfw", False)
                            )
                        elif ch_data["type"] == "voice":
                            await guild.create_voice_channel(
                                name=ch_data["name"],
                                category=existing_cat,
                                bitrate=ch_data.get("bitrate", 64000),
                                user_limit=ch_data.get("user_limit", 0)
                            )

            embed = discord.Embed(
                title="🛡️ Restauración Completada",
                description="Se han recreado los roles y canales faltantes basados en el archivo de respaldo.",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error al restaurar el servidor: {e}", ephemeral=True)

    @backup_crear.error
    @backup_restaurar.error
    async def backup_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Necesitas permisos de **Administrador** para usar este comando.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerBackup(bot))