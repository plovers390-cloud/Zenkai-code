"""
Main bot file - Entry point for the Discord bot
"""

import discord
from discord.ext import commands
import asyncio
import os
import sys
import asyncpg
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.config import Config
from utils.emotes import Emotes

# ------------------ DATABASE CONNECTION ------------------ #
async def ensure_database_exists():
    """Ensure PostgreSQL database connection and create tables if needed."""
    try:
        pool = await asyncpg.create_pool(
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            min_size=1,
            max_size=5
        )
        globals()["_db_pool"] = pool
        print(f"{Emotes.SUCCESS} Connected to PostgreSQL database successfully!")
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}")

async def close_pool():
    """Close PostgreSQL connection pool."""
    pool = globals().get("_db_pool")
    if pool:
        await pool.close()
        print(f"{Emotes.SUCCESS} PostgreSQL pool closed!")

class CustomBot(commands.Bot):
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.start_time = datetime.utcnow()
        self.status_rotation= [
        "Listening $help",
        "Powered by LazyCoder",
        "Serving {servers} servers",
        "24x7 for music",
        "Lazy coder is love ❤️"
        ]
    async def setup_hook(self):
        print(f"Starting Bot...")
        try:
            await ensure_database_exists()
        except Exception as e:
            print(f"{Emotes.ERROR} Database connection failed: {e}")
            print(f"{Emotes.WARNING} Bot will continue but features may not work!")

        await self.load_cogs()
        try:
            await self.tree.sync()
            print(f"{Emotes.SUCCESS} Commands synced!")
        except Exception as e:
            print(f"{Emotes.WARNING} Command sync failed: {e}")
        
        print(f"\n{Emotes.SUCCESS} Bot setup complete!")
        print("=" * 50)

    async def load_cogs(self):
        """Auto load all cogs from src/cogs/customaddons"""
        cogs_dir = os.path.join("src", "cogs", "customaddons")

        if not os.path.exists(cogs_dir):
            print(f"{Emotes.ERROR} Cogs directory not found: {cogs_dir}")
            return

        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_path = f"cogs.customaddons.{filename[:-3]}"
                try:
                    await self.load_extension(cog_path)
                    print(f"  {Emotes.SUCCESS} Loaded: {cog_path}")
                except Exception as e:
                    print(f"  {Emotes.ERROR} Failed to load {cog_path}: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f"{Emotes.SUCCESS} Bot is ready!")
        print(f"📝 Name: {self.user}")
        print(f"🆔 ID: {self.user.id}")
        print(f"🌐 Servers: {len(self.guilds)}")
        print(f"👥 Users: {sum(g.member_count for g in self.guilds)}")
        print(f"⏰ Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        async def rotate_status():
         await self.wait_until_ready()
         index = 0
         while not self.is_closed():
             status_text = self.status_rotation[index % len(self.status_rotation)]
             status_text = status_text.format(servers=len(self.guilds))
        
             await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=status_text
                ),
                status=discord.Status.online
        
             )
             index += 1
             await asyncio.sleep(10)  # change every 10 sec

        self.loop.create_task(rotate_status())

    async def close(self):
        """Close PostgreSQL before shutting down"""
        print(f"\n{Emotes.LOADING} Shutting down...")
        await close_pool()
        await super().close()


@commands.command(name="stats", aliases=["info"])
async def stats(ctx: commands.Context):
    uptime = datetime.utcnow() - ctx.bot.start_time
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    embed = discord.Embed(
        title="Bot Statistics",
        color=discord.Color.pink(),
        timestamp=datetime.utcnow()
    )
    embed.description = (
        f"• Servers: `{len(ctx.bot.guilds)}`\n"
        f"• Users: `{sum(g.member_count for g in ctx.bot.guilds)}`\n"
        f"• Uptime: `{h}h {m}m {s}s`\n"
        f"• Latency: `{round(ctx.bot.latency * 1000)}ms`"
    )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@commands.command(name="help")
async def help_command(ctx: commands.Context):
    embed = discord.Embed(
        title="Help Menu",
        color=discord.Color.pink(),
        timestamp=datetime.utcnow()
    )
    embed.description = (
        f"**<a:ruby66:1431646044869099600> Music Commands**\n"
        f"• `{ctx.prefix}play <song>` — Play music\n"
        f"• `{ctx.prefix}pause` — Pause/Resume\n"
        f"• `{ctx.prefix}skip` — Skip current song\n"
        f"• `{ctx.prefix}stop` — Stop and clear queue\n"
        f"• `{ctx.prefix}queue` — Show queue\n"
        f"• `{ctx.prefix}nowplaying` — See current song\n"
        f"• `{ctx.prefix}volume <0-200>` — Set volume\n"
        f"• `{ctx.prefix}shuffle` — Shuffle queue\n"
        f"• `{ctx.prefix}loop <off/track/queue>` — Repeat mode\n"
        f"• `{ctx.prefix}filter <name>` — Apply audio filters\n"
        f"• `{ctx.prefix}equalizer <preset>` — EQ Presets\n\n"

        f"**<a:ruby66:1431646044869099600> Welcome Commands**\n"
        f"• `{ctx.prefix}welcome setup #channel` — Setup welcome system\n"
        f"• `{ctx.prefix}welcome edit <component> <value>` — Edit embed\n"
        f"• `{ctx.prefix}welcome preview` — Preview current embed\n"
        f"• `{ctx.prefix}welcome disable` — Disable welcome\n"
        f"• `{ctx.prefix}welcome settings` — View settings\n"
        f"• `{ctx.prefix}goodbye_setup #channel <msg>` — Setup goodbye system\n\n"

        f"**<a:ruby66:1431646044869099600> Ticket Commands**\n"
        f"• `{ctx.prefix}ticket setup` — Setup ticket panel\n"
        f"• `{ctx.prefix}ticket create` — Create a ticket\n"
        f"• `{ctx.prefix}ticket close` — Close a ticket\n"

        f"\n**<a:ruby66:1431646044869099600> Utility Commands**\n"
        f"• `{ctx.prefix}stats` — Show bot stats"
    )
    embed.set_footer(text=f"Prefix: {ctx.prefix} | Requested by {ctx.author}")
    await ctx.send(embed=embed)

def main():
    if not Config.BOT_TOKEN:
        print(f"{Emotes.ERROR} Bot token missing! Please set it in config.py or .env")
        return

    print(f"\n{Emotes.INFO} Bot Configuration:")
    print(f" • Prefix: {Config.BOT_PREFIX}")

    bot = CustomBot()
    bot.add_command(stats)
    bot.add_command(help_command)

    try:
        bot.run(Config.BOT_TOKEN)
    except Exception as e:
        print(f"{Emotes.ERROR} Failed to start bot: {e}")

if __name__ == "__main__":
    main()
