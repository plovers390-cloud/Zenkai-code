import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from typing import Optional
import io

from utils.models.customutils import TicketManager
from utils.config import Config
from utils.emotes import Emotes

# ======================= MAIN TICKET PANEL =======================
class TicketMainPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Button Ticket", style=discord.ButtonStyle.green, emoji="🎟️", custom_id="ticket:main_button")
    async def button_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ChannelSelectModal(ticket_type="button")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Dropdown Ticket", style=discord.ButtonStyle.blurple, emoji="📂", custom_id="ticket:main_dropdown")
    async def dropdown_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ChannelSelectModal(ticket_type="dropdown")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Ticket Stats", style=discord.ButtonStyle.grey, emoji="📊", custom_id="ticket:main_stats")
    async def ticket_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        stats = await TicketManager.get_ticket_stats(interaction.guild.id)
        embed = discord.Embed(
            title="📊 Ticket Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Total Tickets", value=f"`{stats['total']}`", inline=True)
        embed.add_field(name="Open Tickets", value=f"`{stats['open']}`", inline=True)
        embed.add_field(name="Closed Tickets", value=f"`{stats['closed']}`", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ======================= CHANNEL SELECT MODAL =======================
class ChannelSelectModal(discord.ui.Modal, title="Setup Ticket Panel"):
    channel_input = discord.ui.TextInput(
        label="Channel ID or Mention",
        placeholder="Enter channel ID or #channel-name",
        required=True,
        style=discord.TextStyle.short
    )

    def __init__(self, ticket_type: str):
        super().__init__()
        self.ticket_type = ticket_type

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

        # Create Ticket Manager Role
        role = discord.utils.get(interaction.guild.roles, name="Ticket Manager")
        if not role:
            role = await interaction.guild.create_role(
                name="Ticket Manager",
                color=discord.Color.blue(),
                permissions=discord.Permissions(manage_channels=True, manage_messages=True)
            )

        # Send appropriate panel
        if self.ticket_type == "button":
            embed = discord.Embed(
                title="🎟️ Support Ticket System",
                description="Click the button below to create a support ticket.\nOur team will assist you shortly!",
                color=discord.Color.green()
            )
            embed.set_footer(text="Button Ticket Panel")
            await channel.send(embed=embed, view=ButtonTicketPanel())
            await interaction.response.send_message(f"✅ Button Ticket Panel created in {channel.mention}!", ephemeral=True)
        else:
            embed = discord.Embed(
                title="📂 Support Ticket System",
                description="Select a category from the dropdown below to create your ticket.",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Dropdown Ticket Panel")
            await channel.send(embed=embed, view=DropdownTicketPanel())
            await interaction.response.send_message(f"✅ Dropdown Ticket Panel created in {channel.mention}!", ephemeral=True)

# ======================= BUTTON PANEL =======================
class ButtonTicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket:create_button")
    async def create_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Ticket")
        await cog.create_ticket_from_panel(interaction, "General Support")

# ======================= DROPDOWN PANEL =======================
class TicketTypeDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", value="General Support", emoji="🆘", description="Get help with general issues"),
            discord.SelectOption(label="Giveaway Claim", value="Giveaway Claim", emoji="🎉", description="Claim your giveaway prize"),
            discord.SelectOption(label="Staff Application", value="Staff Application", emoji="🛠️", description="Apply for staff position"),
            discord.SelectOption(label="Report Issue", value="Report Issue", emoji="⚠️", description="Report a problem or user"),
        ]
        super().__init__(placeholder="Select ticket category...", min_values=1, max_values=1, options=options, custom_id="ticket:dropdown_select")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]  # Already a string, no need for .label
        cog = interaction.client.get_cog("Ticket")
        await cog.create_ticket_from_panel(interaction, category)

class DropdownTicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeDropdown())

# ======================= TICKET CONTROL PANEL =======================
class TicketControlView(discord.ui.View):
    def __init__(self, bot, ticket_number: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_number = ticket_number

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, emoji="🔒", custom_id="ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = await TicketManager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message("❌ Not a valid ticket channel!", ephemeral=True)

        close_view = CloseConfirmView(self.ticket_number)
        await interaction.response.send_message("⚠️ Are you sure you want to close this ticket?", view=close_view, ephemeral=True)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.grey, emoji="✋", custom_id="ticket:claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = await TicketManager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message("❌ Not a valid ticket channel!", ephemeral=True)

        if ticket.get("claimed_by"):
            claimer = interaction.guild.get_member(ticket["claimed_by"])
            return await interaction.response.send_message(f"❌ Ticket already claimed by {claimer.mention if claimer else 'someone'}!", ephemeral=True)

        await TicketManager.claim_ticket(interaction.channel.id, interaction.user.id)

        # Update embed to show claimed status
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"**Claimed by:** {interaction.user.mention}\n**Status:** Active",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        # Get original message and update it
        async for message in interaction.channel.history(limit=10):
            if message.author == self.bot.user and message.embeds:
                await message.edit(embed=embed)
                break

        await interaction.response.send_message(f"✅ {interaction.user.mention} has claimed this ticket!", ephemeral=False)

# ======================= CLOSE CONFIRM =======================
class CloseConfirmView(discord.ui.View):
    def __init__(self, ticket_number: int):
        super().__init__(timeout=30)
        self.ticket_number = ticket_number

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.red, emoji="✔️")
    async def confirm(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        
        # Update ticket in database
        await TicketManager.close_ticket(interaction.channel.id, interaction.user.id)
        
        # Rename channel
        await interaction.channel.edit(name=f"closed-ticket-{self.ticket_number}")
        
        # Send close message with transcript and delete
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"This ticket has been closed by {interaction.user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        await interaction.followup.send(embed=embed, view=TranscriptDeleteView())

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button):
        await interaction.response.send_message("❌ Close cancelled!", ephemeral=True)
        self.stop()

# ======================= TRANSCRIPT & DELETE =======================
class TranscriptDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.blurple, emoji="📜", custom_id="ticket:transcript")
    async def transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Generate transcript
        messages = []
        async for message in interaction.channel.history(limit=500, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = message.content or "[Embed/Attachment]"
            messages.append(f"[{timestamp}] {message.author}: {content}")
        
        transcript_text = "\n".join(messages)
        file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"transcript-{interaction.channel.name}.txt")
        
        await interaction.followup.send("📜 Ticket transcript:", file=file, ephemeral=True)

    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.red, emoji="🗑️", custom_id="ticket:delete")
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Deleting channel in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user}")

# ======================= TICKET COG =======================
class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_manager_role_id = None

    async def cog_load(self):
        await TicketManager.init_db()

        # Auto-create Ticket Manager role for all guilds
        for guild in self.bot.guilds:
            role = discord.utils.get(guild.roles, name="Ticket Manager")
            if not role:
                role = await guild.create_role(
                    name="Ticket Manager",
                    color=discord.Color.blue(),
                    permissions=discord.Permissions(manage_channels=True, manage_messages=True)
                )
            self.ticket_manager_role_id = role.id

        # Register persistent views
        self.bot.add_view(TicketMainPanel())
        self.bot.add_view(ButtonTicketPanel())
        self.bot.add_view(DropdownTicketPanel())

    async def create_ticket_from_panel(self, interaction: discord.Interaction, category_name: str):
        await interaction.response.defer(ephemeral=True)

        # Check for existing ticket
        existing = await TicketManager.get_user_ticket(interaction.guild.id, interaction.user.id)
        if existing:
            channel = interaction.guild.get_channel(existing['channel_id'])
            if channel:
                return await interaction.followup.send(f"❌ You already have an open ticket: {channel.mention}", ephemeral=True)

        # Get or create Tickets category
        cat = discord.utils.get(interaction.guild.categories, name="Tickets")
        if not cat:
            cat = await interaction.guild.create_category("Tickets")

        # Get ticket count
        count = await TicketManager.get_ticket_count(interaction.guild.id) + 1

        # Get Ticket Manager role
        manager_role = discord.utils.get(interaction.guild.roles, name="Ticket Manager")

        # Create ticket channel with proper permissions
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        if manager_role:
            overwrites[manager_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)

        ticket_channel = await cat.create_text_channel(
            name=f"{interaction.user.name}-ticket-{count}",
            overwrites=overwrites
        )

        # Save to database
        await TicketManager.create_ticket(interaction.guild.id, interaction.user.id, ticket_channel.id, count)

        # Create embed
        embed = discord.Embed(
            title=f"🎫 {category_name}",
            description=(
                f"**Ticket Number:** `#{count}`\n"
                f"**Created by:** {interaction.user.mention}\n"
                f"**Category:** {category_name}\n\n"
                "Our support team will assist you shortly!\n"
                "Use the buttons below to manage this ticket."
            ),
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Ticket #{count}")

        # Send ticket message
        await ticket_channel.send(
            f"{interaction.user.mention} {manager_role.mention if manager_role else ''}",
            embed=embed,
            view=TicketControlView(self.bot, count)
        )

        await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

    @commands.command(name="ticket", aliases=["t"])
    async def ticket_command(self, ctx):
        """Open the ticket panel"""
        embed = discord.Embed(
            title="🎟️ Ticket System Panel",
            description=(
                "Choose an option below to setup your ticket system:\n\n"
                "🎟️ **Button Ticket** - Create a simple button-based ticket panel\n"
                "📂 **Dropdown Ticket** - Create a category-based dropdown ticket panel\n"
                "📊 **Ticket Stats** - View ticket statistics"
            ),
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed, view=TicketMainPanel())

# ======================= SETUP =======================
async def setup(bot):
    await bot.add_cog(Ticket(bot))