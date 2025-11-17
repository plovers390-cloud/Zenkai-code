import discord
from discord import app_commands
from discord.ext import commands
import lavalink
from cogs.customaddons.music import LavalinkVoiceClient

class SlashMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.lavalink_voice_client = LavalinkVoiceClient
    # ----------------------- VOICE CHECK -----------------------
    async def ensure_voice(self, interaction):
        player = self.bot.lavalink.player_manager.create(interaction.guild.id)

        if not interaction.user.voice:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:Natsukino:1438720817776169060> | You must be in a voice channel!",
                    color=discord.Color.pink()
                ),
                ephemeral=True
            )
            return None

        if not player.is_connected:
            channel = interaction.user.voice.channel
            player.store("channel", interaction.channel_id)
            await channel.connect(cls=self.bot.lavalink_voice_client)
        
        return player

    # ----------------------- /play -----------------------
    @app_commands.command(name="play", description="Play a song by link or name")
    @app_commands.describe(query="Song name or URL")
    async def play(self, interaction: discord.Interaction, query: str):
        player = await self.ensure_voice(interaction)
        if not player:
            return

        query = query.strip("<>")
        if not query.startswith("http"):
            query = f"ytsearch:{query}"

        results = await player.node.get_tracks(query)

        if not results or not results.tracks:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:Natsukino:1438720817776169060> | No results found!",
                    color=discord.Color.pink()
                ),
                ephemeral=True
            )

        track = results.tracks[0]
        player.add(requester=interaction.user.id, track=track)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"<:Natsukicheck:1438718749409673246> | Added to Queue: **[{track.title}]({track.uri})**",
                color=discord.Color.pink()
            )
        )

        if not player.is_playing:
            await player.play()

    # ----------------------- /stop -----------------------
    @app_commands.command(name="stop", description="Stop playing and clear queue")
    async def stop(self, interaction: discord.Interaction):
        player = await self.ensure_voice(interaction)
        if not player:
            return
        
        player.queue.clear()
        await player.stop()

        await interaction.response.send_message(
            embed=discord.Embed(
                description="<:Natsukicheck:1438718749409673246> | Stopped and queue cleared!",
                color=discord.Color.pink()
            )
        )

    # ----------------------- /skip -----------------------
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        player = await self.ensure_voice(interaction)
        if not player:
            return
        
        await player.skip()

        await interaction.response.send_message(
            embed=discord.Embed(
                description="<:Natsukicheck:1438718749409673246> | Song skipped!",
                color=discord.Color.pink()
            )
        )

    # ----------------------- /search -----------------------
    @app_commands.command(name="search", description="Search a song by name")
    @app_commands.describe(query="Song name to search")
    async def search(self, interaction: discord.Interaction, query: str):
        results = await self.bot.lavalink.player_manager.get(interaction.guild.id).node.get_tracks(
            f"ytsearch:{query}"
        )

        if not results or not results.tracks:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:Natsukino:1438720817776169060> | No results found!",
                    color=discord.Color.pink()
                ),
                ephemeral=True
            )

        desc = "\n".join(
            f"`{i+1}.` {t.title}" for i, t in enumerate(results.tracks[:10])
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔎 Search Results",
                description=desc,
                color=discord.Color.pink()
            ),
            ephemeral=True
        )

    # ----------------------- /autoplay -----------------------
    @app_commands.command(name="autoplay", description="Enable or disable autoplay")
    async def autoplay(self, interaction: discord.Interaction):
        player = await self.ensure_voice(interaction)
        if not player:
            return

        current = getattr(player, "autoplay_enabled", False)

        player.autoplay_enabled = not current

        await interaction.response.send_message(
            embed=discord.Embed(
                description="<:Natsukicheck:1438718749409673246> | Autoplay **Enabled!**" if player.autoplay_enabled else "<:Natsukicheck:1438718749409673246> | Autoplay **Disabled!**",
                color=discord.Color.pink()
            )
        )

    # ----------------------- /loop -----------------------
    @app_commands.command(name="loop", description="Enable or disable song loop")
    async def loop(self, interaction: discord.Interaction):
        player = await self.ensure_voice(interaction)
        if not player:
            return

        player.repeat = 0 if player.repeat else 1

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"<:Natsukicheck:1438718749409673246> | Loop {'Enabled' if player.repeat else 'Disabled'}!",
                color=discord.Color.pink()
            )
        )

    # ----------------------- /bass -----------------------
    @app_commands.command(name="bass", description="Toggle bass boost on/off")
    async def bass(self, interaction: discord.Interaction):
        player = await self.ensure_voice(interaction)
        if not player:
            return

        if getattr(player, "bass_enabled", False):
            await player.clear_filters()
            player.bass_enabled = False

            await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:Natsukicheck:1438718749409673246> | Bass Disabled!",
                    color=discord.Color.pink()
                )
            )
        else:
            eq = lavalink.filters.Equalizer()
            eq.update(bands=[
                (0, 0.2), (1, 0.15), (2, 0.1), (3, 0.05), (4, 0.0),
                (5, -0.05), (6, -0.1), (7, -0.1), (8, -0.1), (9, -0.1),
            ])

            await player.set_filter(eq)
            player.bass_enabled = True

            await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:Natsukicheck:1438718749409673246> | Bass Enabled!",
                    color=discord.Color.pink()
                )
            )


async def setup(bot):
    await bot.add_cog(SlashMusic(bot))
