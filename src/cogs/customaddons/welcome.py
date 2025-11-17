import discord
from discord.ext import commands
from datetime import datetime
from typing import Optional
import asyncio

from utils.models.customutils import WelcomeManager
from utils.config import Config
from utils.emotes import Emotes

# ======================= WELCOME SETUP PANEL =======================
class WelcomeSetupPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Default Welcome", style=discord.ButtonStyle.green, emoji="✨", custom_id="welcome:default")
    async def default_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ChannelSelectModal(setup_type="default")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Manual Welcome", style=discord.ButtonStyle.blurple, emoji="✏️", custom_id="welcome:manual")
    async def manual_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ManualWelcomeModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Banner & Thumbnail", style=discord.ButtonStyle.grey, emoji="🖼️", custom_id="welcome:banner_thumb")
    async def banner_thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BannerThumbnailModal()
        await interaction.response.send_modal(modal)

# ======================= CHANNEL SELECT MODAL =======================
class ChannelSelectModal(discord.ui.Modal, title="Select Welcome Channel"):
    channel_input = discord.ui.TextInput(
        label="Channel ID or Mention",
        placeholder="Enter channel ID or #channel-name",
        required=True,
        style=discord.TextStyle.short
    )

    def __init__(self, setup_type: str):
        super().__init__()
        self.setup_type = setup_type

    async def on_submit(self, interaction: discord.Interaction):
        channel_text = self.channel_input.value.strip()
        
        # Parse channel
        channel_id = channel_text.replace("<#", "").replace(">", "")
        try:
            channel = interaction.guild.get_channel(int(channel_id))
        except:
            return await interaction.response.send_message("❌ Invalid channel!", ephemeral=True)

        if not channel:
            return await interaction.response.send_message("❌ Channel not found!", ephemeral=True)

        # Default welcome setup with bot's default message
        default_title = f"👋 Welcome to {interaction.guild.name}!"
        default_description = f"Welcome {{user}}! We're glad to have you here. 🎉\n\nYou are member **#{{membercount}}**"
        default_footer = "Enjoy your stay!"
        default_color = "#00ff00"

        await WelcomeManager.update_settings(
            guild_id=interaction.guild.id,
            enabled=True,
            channel_id=channel.id,
            title=default_title,
            description=default_description,
            footer=default_footer,
            color=default_color
        )

        embed = discord.Embed(
            title="✅ Default Welcome Setup Complete!",
            description=f"Welcome messages will be sent to {channel.mention}\n\n**Default Message Preview:**",
            color=discord.Color.green()
        )
        embed.add_field(name="Title", value=default_title, inline=False)
        embed.add_field(name="Description", value=default_description, inline=False)
        embed.add_field(name="Footer", value=default_footer, inline=False)
        embed.set_footer(text="You can customize this anytime using the Manual Welcome button!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ======================= MANUAL WELCOME MODAL =======================
class ManualWelcomeModal(discord.ui.Modal, title="Manual Welcome Setup"):
    channel_input = discord.ui.TextInput(
        label="Welcome Channel",
        placeholder="#channel or channel ID",
        required=True,
        style=discord.TextStyle.short
    )

    title_input = discord.ui.TextInput(
        label="Welcome Title",
        placeholder="Welcome to our server!",
        required=True,
        style=discord.TextStyle.short,
        max_length=256
    )

    description_input = discord.ui.TextInput(
        label="Welcome Description",
        placeholder="Use {user} for mention, {username} for name, {server} for server name, {membercount} for count",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=2000
    )

    footer_input = discord.ui.TextInput(
        label="Footer Text",
        placeholder="Enjoy your stay!",
        required=False,
        style=discord.TextStyle.short,
        max_length=256
    )

    color_input = discord.ui.TextInput(
        label="Embed Color (hex or name)",
        placeholder="#00ff00 or green",
        required=False,
        style=discord.TextStyle.short,
        default="#00ff00"
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Parse channel
        channel_text = self.channel_input.value.strip()
        channel_id = channel_text.replace("<#", "").replace(">", "")
        try:
            channel = interaction.guild.get_channel(int(channel_id))
        except:
            return await interaction.response.send_message("❌ Invalid channel!", ephemeral=True)

        if not channel:
            return await interaction.response.send_message("❌ Channel not found!", ephemeral=True)

        title = self.title_input.value.strip()
        description = self.description_input.value.strip()
        footer = self.footer_input.value.strip() or "Welcome!"
        color = self.color_input.value.strip() or "#00ff00"

        await WelcomeManager.update_settings(
            guild_id=interaction.guild.id,
            enabled=True,
            channel_id=channel.id,
            title=title,
            description=description,
            footer=footer,
            color=color
        )

        embed = discord.Embed(
            title="✅ Manual Welcome Setup Complete!",
            description=f"Welcome messages will be sent to {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Title", value=title, inline=False)
        embed.add_field(name="Description", value=description[:1024], inline=False)
        embed.add_field(name="Footer", value=footer, inline=False)
        embed.add_field(name="Color", value=color, inline=False)
        embed.set_footer(text="Placeholders: {user} {username} {server} {membercount}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ======================= BANNER & THUMBNAIL MODAL =======================
class BannerThumbnailModal(discord.ui.Modal, title="Banner & Thumbnail Setup"):
    banner_input = discord.ui.TextInput(
        label="Banner Image URL",
        placeholder="https://example.com/banner.png",
        required=False,
        style=discord.TextStyle.short
    )

    thumbnail_input = discord.ui.TextInput(
        label="Thumbnail Image URL",
        placeholder="https://example.com/thumbnail.png (leave empty for user avatar)",
        required=False,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        banner_url = self.banner_input.value.strip()
        thumbnail_url = self.thumbnail_input.value.strip()

        # Validate URLs if provided
        if banner_url and not (banner_url.startswith('http://') or banner_url.startswith('https://')):
            return await interaction.response.send_message("❌ Banner URL must start with http:// or https://", ephemeral=True)
        
        if thumbnail_url and not (thumbnail_url.startswith('http://') or thumbnail_url.startswith('https://')):
            return await interaction.response.send_message("❌ Thumbnail URL must start with http:// or https://", ephemeral=True)

        await WelcomeManager.update_settings(
            guild_id=interaction.guild.id,
            image=banner_url if banner_url else None,
            thumbnail=thumbnail_url if thumbnail_url else None
        )

        embed = discord.Embed(
            title="✅ Banner & Thumbnail Updated!",
            color=discord.Color.green()
        )
        
        if banner_url:
            embed.add_field(name="Banner Image", value="✅ Set", inline=True)
            embed.set_image(url=banner_url)
        else:
            embed.add_field(name="Banner Image", value="❌ Not set", inline=True)
        
        if thumbnail_url:
            embed.add_field(name="Thumbnail", value="✅ Set", inline=True)
            embed.set_thumbnail(url=thumbnail_url)
        else:
            embed.add_field(name="Thumbnail", value="❌ Using user avatar", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ======================= WELCOME COG =======================
class Welcome(commands.Cog):
    """Advanced welcome system with customization"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def cog_load(self):
        """Called when the cog is loaded"""
        await WelcomeManager.init_db()
        self.bot.add_view(WelcomeSetupPanel())
        print(f"{Emotes.SUCCESS} Welcome system loaded!")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Triggered when a member joins the server"""
        if member.bot:
            return
        
        settings = await WelcomeManager.get_settings(member.guild.id)
        if not settings or not settings.get('enabled'):
            return
        
        welcome_channel_id = settings.get('channel_id')
        if not welcome_channel_id:
            return
        
        channel = member.guild.get_channel(welcome_channel_id)
        if not channel:
            return
        
        # Create welcome embed with custom settings
        embed = await self.create_welcome_embed(member, settings)
        
        try:
            await channel.send(content=member.mention, embed=embed)
        except discord.Forbidden:
            print(f"{Emotes.ERROR} No permission to send welcome message in {channel.name}")
    
    async def create_welcome_embed(self, member: discord.Member, settings: dict) -> discord.Embed:
        """Create welcome embed with custom settings"""
        # Get custom values or use defaults
        title = settings.get('title', f"👋 Welcome to {member.guild.name}!")
        description = settings.get('description', f"Welcome {{user}}! We're glad to have you here. 🎉")
        footer = settings.get('footer', "Enjoy your stay!")
        color = self.parse_color(settings.get('color', "#00ff00"))
        
        # Replace placeholders in title
        title = title.replace("{user}", member.mention)
        title = title.replace("{username}", str(member))
        title = title.replace("{server}", member.guild.name)
        title = title.replace("{membercount}", str(member.guild.member_count))
        
        # Replace placeholders in description
        description = description.replace("{user}", member.mention)
        description = description.replace("{username}", str(member))
        description = description.replace("{server}", member.guild.name)
        description = description.replace("{membercount}", str(member.guild.member_count))
        
        # Replace placeholders in footer
        footer = footer.replace("{user}", str(member))
        footer = footer.replace("{username}", str(member))
        footer = footer.replace("{server}", member.guild.name)
        footer = footer.replace("{membercount}", str(member.guild.member_count))
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Set thumbnail (custom or user avatar)
        if settings.get('thumbnail'):
            embed.set_thumbnail(url=settings['thumbnail'])
        elif member.avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
        
        # Set main image (banner)
        if settings.get('image'):
            embed.set_image(url=settings['image'])
        
        # Set footer
        embed.set_footer(text=footer, icon_url=member.display_avatar.url if member.avatar else None)
        
        return embed
    
    def parse_color(self, color_str: str) -> discord.Color:
        """Parse color string to discord.Color"""
        try:
            if color_str.startswith('#'):
                return discord.Color(int(color_str[1:], 16))
            else:
                color_lower = color_str.lower()
                color_map = {
                    'red': discord.Color.red(),
                    'green': discord.Color.green(),
                    'blue': discord.Color.blue(),
                    'gold': discord.Color.gold(),
                    'purple': discord.Color.purple(),
                    'orange': discord.Color.orange(),
                    'teal': discord.Color.teal(),
                    'magenta': discord.Color.magenta(),
                    'dark_red': discord.Color.dark_red(),
                    'dark_green': discord.Color.dark_green(),
                    'dark_blue': discord.Color.dark_blue(),
                    'dark_purple': discord.Color.dark_purple(),
                    'dark_teal': discord.Color.dark_teal(),
                    'dark_magenta': discord.Color.dark_magenta(),
                    'dark_gold': discord.Color.dark_gold(),
                    'dark_orange': discord.Color.dark_orange(),
                }
                return color_map.get(color_lower, discord.Color.green())
        except:
            return discord.Color.green()
    
    @commands.command(name="welcomesetup", aliases=["wsetup", "ws"])
    @commands.has_permissions(administrator=True)
    async def welcome_setup(self, ctx):
        """Open the welcome setup panel"""
        embed = discord.Embed(
            title="👋 Welcome System Setup",
            description=(
                "Choose how you want to setup your welcome system:\n\n"
                "✨ **Default Welcome** - Quick setup with bot's default message\n"
                "✏️ **Manual Welcome** - Customize your own welcome message\n"
                "🖼️ **Banner & Thumbnail** - Set custom banner and thumbnail images\n\n"
                "**Placeholders you can use:**\n"
                "• `{user}` - Mentions the user\n"
                "• `{username}` - User's name\n"
                "• `{server}` - Server name\n"
                "• `{membercount}` - Member count"
            ),
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed, view=WelcomeSetupPanel())

    @commands.command(name="welcometest", aliases=["wtest"])
    @commands.has_permissions(administrator=True)
    async def welcome_test(self, ctx):
        """Test the welcome message"""
        settings = await WelcomeManager.get_settings(ctx.guild.id)
        if not settings or not settings.get('enabled'):
            embed = discord.Embed(
                title=f"{Emotes.ERROR} Welcome System Not Configured",
                description="Use `welcomesetup` to configure the welcome system first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        welcome_channel_id = settings.get('channel_id')
        if not welcome_channel_id:
            embed = discord.Embed(
                title=f"{Emotes.ERROR} No Welcome Channel Set",
                description="Please set a welcome channel first using `welcomesetup`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        channel = ctx.guild.get_channel(welcome_channel_id)
        if not channel:
            embed = discord.Embed(
                title=f"{Emotes.ERROR} Welcome Channel Not Found",
                description="The configured welcome channel no longer exists.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Create welcome embed
        welcome_embed = await self.create_welcome_embed(ctx.author, settings)
        
        try:
            await channel.send(
                content=f"🧪 **TEST MESSAGE** - {ctx.author.mention}",
                embed=welcome_embed
            )
            
            confirm_embed = discord.Embed(
                title=f"{Emotes.SUCCESS} Test Welcome Message Sent!",
                description=f"Check {channel.mention} to see your welcome message.",
                color=discord.Color.green()
            )
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title=f"{Emotes.ERROR} Permission Error",
                description=f"I don't have permission to send messages in {channel.mention}!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="welcomedisable", aliases=["wdisable"])
    @commands.has_permissions(administrator=True)
    async def welcome_disable(self, ctx):
        """Disable welcome system"""
        await WelcomeManager.update_settings(
            guild_id=ctx.guild.id,
            enabled=False
        )
        
        embed = discord.Embed(
            title=f"{Emotes.SUCCESS} Welcome System Disabled",
            description="Welcome messages will no longer be sent when members join.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="welcomestats", aliases=["wstats"])
    @commands.has_permissions(administrator=True)
    async def welcome_stats(self, ctx):
        """View current welcome system settings"""
        settings = await WelcomeManager.get_settings(ctx.guild.id) or {}
        
        embed = discord.Embed(
            title="⚙️ Welcome System Settings",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Status
        embed.add_field(
            name="Status",
            value="✅ Enabled" if settings.get('enabled') else "❌ Disabled",
            inline=True
        )
        
        # Channel
        channel = ctx.guild.get_channel(settings.get('channel_id', 0))
        embed.add_field(
            name="Channel",
            value=channel.mention if channel else "Not set",
            inline=True
        )
        
        # Custom settings
        embed.add_field(
            name="Custom Title",
            value="✅ Set" if settings.get('title') else "❌ Default",
            inline=True
        )
        
        embed.add_field(
            name="Custom Description",
            value="✅ Set" if settings.get('description') else "❌ Default",
            inline=True
        )
        
        embed.add_field(
            name="Banner Image",
            value="✅ Set" if settings.get('image') else "❌ Not set",
            inline=True
        )
        
        embed.add_field(
            name="Thumbnail",
            value="✅ Set" if settings.get('thumbnail') else "❌ User Avatar",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))