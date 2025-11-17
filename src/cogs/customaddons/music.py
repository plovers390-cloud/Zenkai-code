import discord
from discord.ext import commands
import lavalink
from lavalink.filters import Equalizer
import re, aiohttp, asyncio, datetime

# Regex for URLs
url_rx = re.compile(r'https?://(?:www\.)?.+')

# ---------------------------------------------------------
#                 CUSTOM VOICE CLIENT
# ---------------------------------------------------------
class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client, channel):
        self.client = client
        self.channel = channel
        self.guild_id = channel.guild.id

    async def on_voice_server_update(self, data):
        await self.client.lavalink.voice_update_handler({
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        })

    async def on_voice_state_update(self, data):
        await self.client.lavalink.voice_update_handler({
            't': 'VOICE_STATE_UPDATE',
            'd': data
        })

    async def connect(self, *, timeout, reconnect, self_deaf=True, self_mute=False):
        self.client.lavalink.player_manager.create(self.guild_id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_deaf=True)

    async def disconnect(self, *, force=False):
        player = self.client.lavalink.player_manager.get(self.guild_id)
        if not force and not player.is_connected: return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()


# ---------------------------------------------------------
#                 FILTER DROPDOWN
# ---------------------------------------------------------
class FilterDropdown(discord.ui.Select):
    def __init__(self, player):
        self.player = player

        options = [
            discord.SelectOption(label="8D Audio", value="8d", emoji="🎧"),
            discord.SelectOption(label="Piano", value="piano", emoji="🎹"),
            discord.SelectOption(label="Metal", value="metal", emoji="🤘"),
            discord.SelectOption(label="Rock", value="rock", emoji="🎸"),
            discord.SelectOption(label="Bass Boost", value="bass", emoji="🔊"),
            discord.SelectOption(label="Vocal Boost", value="vocal", emoji="🎤"),
            discord.SelectOption(label="Flat (Reset EQ)", value="flat", emoji="📊"),
            discord.SelectOption(label="Reset All Filters", value="reset", emoji="🔄"),
        ]

        super().__init__(
            placeholder="🎛 Select an Audio Filter",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction):
        choice = self.values[0]
        eq = Equalizer()

        if choice == "reset":
            await self.player.clear_filters()
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="🔄 | **All Filters Reset!**",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )

        presets = {
            "8d": [(i, 0.15 if i % 2 == 0 else -0.15) for i in range(15)],
            "piano": [(0, -0.25), (1, -0.25), (2, -0.12), (3, 0.0), (4, 0.25)],
            "metal": [(1, 0.1), (2, 0.15), (3, 0.15)],
            "rock": [(0, 0.20), (1, 0.15), (2, 0.10)],
            "bass": [(0, 0.25), (1, 0.20), (2, 0.15)],
            "vocal": [(10, 0.20), (11, 0.25), (12, 0.30)],
            "flat": [(i, 0.0) for i in range(15)]
        }

        bands = presets.get(choice, [(0, 0)])

        eq.update(bands=bands)
        await self.player.set_filter(eq)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"<:Natsukicheck:1438718749409673246> | **{choice.upper()} Filter Applied!**",
                color=discord.Color.green()
            ),
            ephemeral=True
        )


# ---------------------------------------------------------
#                 NOW PLAYING CONTROL BUTTONS
# ---------------------------------------------------------
class ControlView(discord.ui.View):
    def __init__(self, bot, player):
        super().__init__(timeout=None)
        self.bot = bot
        self.player = player

    # ⏯️ Pause / Resume
    @discord.ui.button(label="❚❚", style=discord.ButtonStyle.secondary, custom_id="pause_btn")
    async def pause(self, interaction, btn):
        await self.player.set_pause(not self.player.paused)
        
        if self.player.paused:
            btn.label = "▶"
            msg = "Paused"
        else:
            btn.label = "❚❚"
            msg = "Resumed"
            
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=discord.Embed(description=f"⏭ | {msg}!", color=0x2b2d31),
            ephemeral=True
        )

    # ⏭️ Skip
    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary, custom_id="skip_btn")
    async def skip(self, interaction, btn):
        await self.player.skip()
        await interaction.response.send_message(
            embed=discord.Embed(description="⏭ | Skipped!", color=0x2b2d31),
            ephemeral=True
        )

    # 🔁 Loop
    @discord.ui.button(label="🗘", style=discord.ButtonStyle.secondary, custom_id="loop_btn")
    async def loop(self, interaction, btn):
        self.player.loop = 0 if self.player.loop else 1
        
        if self.player.loop:
            btn.style = discord.ButtonStyle.success
            msg = "Enabled"
        else:
            btn.style = discord.ButtonStyle.secondary
            msg = "Disabled"
            
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=discord.Embed(description=f"🗘 | Loop {msg}", color=0x2b2d31),
            ephemeral=True
        )

    # 🔀 Shuffle
    @discord.ui.button(label="⇄", style=discord.ButtonStyle.secondary, custom_id="shuffle_btn")
    async def shuffle(self, interaction, btn):
        self.player.shuffle = not self.player.shuffle
        
        if self.player.shuffle:
            btn.style = discord.ButtonStyle.success
            msg = "On"
        else:
            btn.style = discord.ButtonStyle.secondary
            msg = "Off"
            
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=discord.Embed(description=f"⇄ | Shuffle {msg}", color=0x2b2d31),
            ephemeral=True
        )

    # 💾 Queue
    @discord.ui.button(label="📃", style=discord.ButtonStyle.secondary, custom_id="queue_btn")
    async def show_queue(self, interaction, btn):
        if not self.player.queue:
            return await interaction.response.send_message(
                embed=discord.Embed(description="📃 Queue is Empty!", color=0x2b2d31),
                ephemeral=True
            )

        desc = "\n".join(
            [f"`{i+1}.` **{t.title[:40]}...**" if len(t.title) > 40 else f"`{i+1}.` **{t.title}**" 
             for i, t in enumerate(self.player.queue[:10])]
        )
        
        total = len(self.player.queue)
        footer_text = f"Showing 10 of {total} tracks" if total > 10 else f"{total} track(s) in queue"

        embed = discord.Embed(
            title="📃 Queue",
            description=desc,
            color=0x2b2d31
        )
        embed.set_footer(text=footer_text)

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------------------------------------------------
#                      MUSIC COG
# ---------------------------------------------------------
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Init Lavalink
        if not hasattr(bot, "lavalink"):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(
                host='23.80.88.110',
                port=6561,
                password='youshallnotpass',
                region='india',
                name='main'
            )
            bot.add_listener(bot.lavalink.voice_update_handler, "on_socket_response")

        bot.lavalink.add_event_hook(self.track_hook)

    # ---------------------------------------------------------
    async def ensure_voice(self, ctx):
        player = self.bot.lavalink.player_manager.create(ctx.guild.id)

        if not ctx.author.voice:
            await ctx.send("Join a voice channel first!")
            return False

        if not player.is_connected:
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
            player.store("channel", ctx.channel.id)

        return True

    # ---------------------------------------------------------
    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query):
        if not await self.ensure_voice(ctx):
            return

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not url_rx.match(query):
            query = f"ytmsearch:{query}"

        results = await player.node.get_tracks(query)
        if not results.tracks:
            return await ctx.send("No results found.")

        track = results.tracks[0]
        player.add(requester=ctx.author.id, track=track)

        embed = discord.Embed(
            description=f"<:Natsukicheck:1438718749409673246> | Added **{track.title}** to queue!",
            color=0x2b2d31
        )
        await ctx.send(embed=embed)

        if not player.is_playing:
            await player.play()

    # ---------------------------------------------------------
    @commands.command()
    async def filter(self, ctx):
        """Show the filter menu"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        view = discord.ui.View()
        view.add_item(FilterDropdown(player))

        embed = discord.Embed(
            title="🎛️ Audio Filters",
            description="Choose a filter below:",
            color=0x2b2d31
        )

        await ctx.send(embed=embed, view=view)

    # ---------------------------------------------------------
    @commands.command(aliases=["np", "current"])
    async def nowplaying(self, ctx):
        """Show currently playing track"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.current:
            return await ctx.send("Nothing is playing!")

        track = player.current
        
        # Create modern embed with side thumbnail
        embed = discord.Embed(color=0x2b2d31)
        
        # Header with bullet point style
        embed.description = (
            f"### • **Now Playing**\n"
            f"**○ {track.title}**\n\n"
            f"**○ By:** {track.author}\n"
            f"**○ Duration:** `{self.format_time(track.duration)}`\n"
            f"**○ Requested by:** {ctx.guild.get_member(track.requester).mention}"
        )
        
        # Thumbnail on right side
        embed.set_thumbnail(url=f"https://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg")
        
        # Footer with timestamp
        embed.set_footer(
            text=f"Playing since • {datetime.datetime.now().strftime('%I:%M %p')}",
            icon_url=ctx.guild.get_member(track.requester).display_avatar.url
        )

        view = ControlView(self.bot, player)
        await ctx.send(embed=embed, view=view)

    # ---------------------------------------------------------
    @commands.command()
    async def queue(self, ctx, page: int = 1):
        """Show queue with pagination"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.queue:
            return await ctx.send("Queue is empty!")
        
        items_per_page = 10
        pages = (len(player.queue) + items_per_page - 1) // items_per_page
        
        if page < 1 or page > pages:
            page = 1
        
        start = (page - 1) * items_per_page
        end = start + items_per_page
        
        desc = "\n".join(
            [f"`{i+1}.` **{t.title}** - `{self.format_time(t.duration)}`" 
             for i, t in enumerate(player.queue[start:end], start=start)]
        )
        
        embed = discord.Embed(
            title=f"🧾 Queue - Page {page}/{pages}",
            description=desc,
            color=0x2b2d31
        )
        
        if player.current:
            embed.add_field(
                name="♫ Now Playing",
                value=f"**{player.current.title}**",
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(player.queue)} tracks")
        await ctx.send(embed=embed)

    # ---------------------------------------------------------
    @commands.command()
    async def volume(self, ctx, vol: int = None):
        """Set volume (0-100)"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if vol is None:
            return await ctx.send(f"Current volume: **{player.volume}%**")
        
        if vol < 0 or vol > 100:
            return await ctx.send("Volume must be between 0-100!")
        
        await player.set_volume(vol)
        
        embed = discord.Embed(
            description=f"<:Natsukicheck:1438718749409673246> Volume set to **{vol}%**",
            color=0x2b2d31
        )
        await ctx.send(embed=embed)

    # ---------------------------------------------------------
    async def track_hook(self, event):
        if isinstance(event, lavalink.events.TrackStartEvent):
            player = event.player
            channel_id = player.fetch("channel")
            if not channel_id:
                return
                
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
                
            track = event.track

            # Modern "Now Playing" embed with side thumbnail
            embed = discord.Embed(color=0x2b2d31)
            
            # Bullet point style description
            embed.description = (
                f"### • **Now Playing**\n"
                f"**○ {track.title}**\n\n"
                f"**○ By:** {track.author}\n"
                f"**○ Duration:** `{self.format_time(track.duration)}`\n"
                f"**○ Requested by:** <@{track.requester}>"
            )
            
            # Thumbnail on the right side (like your image)
            embed.set_thumbnail(url=f"https://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg")
            
            # Footer with user avatar and timestamp
            requester = channel.guild.get_member(track.requester)
            if requester:
                embed.set_footer(
                    text=f"Requested by {requester.name} • {datetime.datetime.now().strftime('%I:%M %p')}",
                    icon_url=requester.display_avatar.url
                )

            view = ControlView(self.bot, player)
            await channel.send(embed=embed, view=view)

        if isinstance(event, lavalink.events.TrackEndEvent):
            player=event.player

            await asyncio.sleep(1)

            if not player.current and not player.queue:
                channel_id = player.fetch("channel")
                if not channel_id:
                    return
                
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    return

                embed=discord.Embed(
                    description=f"<:Natsukicheck:1438718749409673246> | **Queue finished! Add more songs to continue playing.**",
                    color=discord.Color.pink()
                )
                await channel.send(embed=embed)
    # ---------------------------------------------------------
    def format_time(self, ms):
        s = (ms // 1000) % 60
        m = (ms // 60000) % 60
        h = (ms // 3600000)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# ---------------------------------------------------------
async def setup(bot):
    await bot.add_cog(Music(bot))