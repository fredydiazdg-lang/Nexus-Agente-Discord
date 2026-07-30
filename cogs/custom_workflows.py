import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class CustomWorkflows(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.workflows_file = "workflows_data.json"

    def _load_workflows(self):
        if os.path.exists(self.workflows_file):
            try:
                with open(self.workflows_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando workflows: {e}")
        return {}

    def _save_workflows(self, data):
        with open(self.workflows_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    workflow_group = app_commands.Group(name="flujo", description="Creador de automatizaciones personalizadas")

    @workflow_group.command(name="crear_respuesta", description="Crea una auto-respuesta cuando alguien dice una palabra clave")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(palabra_clave="La palabra o frase que activa la regla", respuesta="La respuesta que dará el bot")
    async def crear_respuesta(self, interaction: discord.Interaction, palabra_clave: str, respuesta: str):
        workflows = self._load_workflows()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in workflows:
            workflows[guild_id] = {"triggers": {}}

        trigger_clean = palabra_clave.lower().strip()
        workflows[guild_id]["triggers"][trigger_clean] = respuesta
        self._save_workflows(workflows)

        embed = discord.Embed(
            title="⚡ Automatización Creada",
            description=f"**Palabra Clave:** `{trigger_clean}`\n**Respuesta:** {respuesta}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @workflow_group.command(name="lista", description="Muestra las automatizaciones activas en este servidor")
    async def listar_flujos(self, interaction: discord.Interaction):
        workflows = self._load_workflows()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in workflows or not workflows[guild_id].get("triggers"):
            await interaction.response.send_message("❌ No hay automatizaciones creadas en este servidor.", ephemeral=True)
            return

        triggers = workflows[guild_id]["triggers"]
        texto = ""
        for i, (kw, resp) in enumerate(triggers.items(), 1):
            texto += f"`{i}.` **{kw}** ➔ {resp}\n"

        embed = discord.Embed(
            title="⚙️ Flujos y Respuestas Automáticas",
            description=texto,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        workflows = self._load_workflows()
        guild_id = str(message.guild.id)
        
        if guild_id in workflows and "triggers" in workflows[guild_id]:
            contenido = message.content.lower()
            triggers = workflows[guild_id]["triggers"]

            for kw, resp in triggers.items():
                if kw in contenido:
                    await message.channel.send(f"{message.author.mention}, {resp}")
                    break

async def setup(bot):
    await bot.add_cog(CustomWorkflows(bot))