"""
Emotes and icons for the bot
Replace with your custom emote IDs from your server
Format: <:name:id> for static, <a:name:id> for animated
"""

class Emotes:
    """Custom emote class - Replace IDs with your server's emotes"""
    
    # ==================== STATUS EMOTES ====================
    # Success/Error/Info
    SUCCESS = "✅"  # Replace with <:success:123456789>
    ERROR = "❌"    # Replace with <:error:123456789>
    WARNING = "⚠️"  # Replace with <:warning:123456789>
    INFO = "ℹ️"     # Replace with <:info:123456789>
    LOADING = "⏳"  # Replace with <a:loading:123456789>
    
    # ==================== TICKET EMOTES ====================
    TICKET = "🎫"       # Replace with <:ticket:123456789>
    TICKET_OPEN = "📂"  # Replace with <:ticket_open:123456789>
    TICKET_CLOSED = "📁" # Replace with <:ticket_closed:123456789>
    CLAIM = "✋"        # Replace with <:claim:123456789>
    LOCK = "🔒"        # Replace with <:lock:123456789>
    UNLOCK = "🔓"      # Replace with <:unlock:123456789>
    
    # ==================== WELCOME EMOTES ====================
    WAVE = "👋"        # Replace with <:wave:123456789>
    WELCOME = "🎉"     # Replace with <:welcome:123456789>
    GOODBYE = "😢"     # Replace with <:goodbye:123456789>
    VERIFY = "✅"      # Replace with <:verify:123456789>
    MEMBER = "👤"      # Replace with <:member:123456789>
    
    # ==================== MODERATION EMOTES ====================
    BAN = "🔨"         # Replace with <:ban:123456789>
    KICK = "👢"        # Replace with <:kick:123456789>
    MUTE = "🔇"        # Replace with <:mute:123456789>
    UNMUTE = "🔊"      # Replace with <:unmute:123456789>
    WARN = "⚠️"        # Replace with <:warn:123456789>
    
    # ==================== UTILITY EMOTES ====================
    SETTINGS = "⚙️"    # Replace with <:settings:123456789>
    SEARCH = "🔍"      # Replace with <:search:123456789>
    LINK = "🔗"        # Replace with <:link:123456789>
    EDIT = "✏️"        # Replace with <:edit:123456789>
    DELETE = "🗑️"      # Replace with <:delete:123456789>
    PIN = "📌"         # Replace with <:pin:123456789>
    
    # ==================== REACTION EMOTES ====================
    UPVOTE = "⬆️"      # Replace with <:upvote:123456789>
    DOWNVOTE = "⬇️"    # Replace with <:downvote:123456789>
    LIKE = "❤️"        # Replace with <:like:123456789>
    DISLIKE = "💔"     # Replace with <:dislike:123456789>
    
    # ==================== CATEGORY EMOTES ====================
    GAMING = "🎮"      # Replace with <:gaming:123456789>
    MUSIC = "🎵"       # Replace with <:music:123456789>
    ART = "🎨"         # Replace with <:art:123456789>
    TECH = "💻"        # Replace with <:tech:123456789>
    CHAT = "💬"        # Replace with <:chat:123456789>
    
    # ==================== CUSTOM ANIMATED ====================
    # These should be animated emotes
    LOADING_ANIMATED = "⏳"  # Replace with <a:loading:123456789>
    TYPING = "✍️"           # Replace with <a:typing:123456789>
    PARTY = "🎉"            # Replace with <a:party:123456789>
    SPARKLES = "✨"         # Replace with <a:sparkles:123456789>
    
    # ==================== BADGES ====================
    STAFF = "👮"       # Replace with <:staff:123456789>
    OWNER = "👑"       # Replace with <:owner:123456789>
    ADMIN = "🛡️"       # Replace with <:admin:123456789>
    MOD = "🔰"         # Replace with <:mod:123456789>
    VERIFIED = "✅"    # Replace with <:verified:123456789>
    BOOSTER = "💎"     # Replace with <:booster:123456789>
    
    # ==================== MISC ====================
    ARROW_RIGHT = "➡️"  # Replace with <:arrow_right:123456789>
    ARROW_LEFT = "⬅️"   # Replace with <:arrow_left:123456789>
    ARROW_UP = "⬆️"     # Replace with <:arrow_up:123456789>
    ARROW_DOWN = "⬇️"   # Replace with <:arrow_down:123456789>
    DOT = "•"          # Replace with <:dot:123456789>
    BLANK = "⠀"        # Invisible character for spacing
    
    @classmethod
    def get_all_emotes(cls) -> dict:
        """Get all emotes as a dictionary"""
        return {
            name: value 
            for name, value in vars(cls).items() 
            if not name.startswith('_') and not callable(value)
        }
    
    @classmethod
    def format_list(cls, items: list, emote: str = None) -> str:
        """Format a list with emotes"""
        emote = emote or cls.DOT
        return "\n".join(f"{emote} {item}" for item in items)
    
    @classmethod
    def status_text(cls, success: bool) -> str:
        """Get status text with emote"""
        return f"{cls.SUCCESS} Success!" if success else f"{cls.ERROR} Failed!"


class Icons:
    """Icon URLs for embeds"""
    
    # Default icons
    DEFAULT_AVATAR = "https://cdn.discordapp.com/embed/avatars/0.png"
    DEFAULT_GUILD = "https://cdn.discordapp.com/embed/avatars/1.png"
    
    # Status icons
    ONLINE = "https://cdn.discordapp.com/emojis/123456789.png"
    IDLE = "https://cdn.discordapp.com/emojis/123456789.png"
    DND = "https://cdn.discordapp.com/emojis/123456789.png"
    OFFLINE = "https://cdn.discordapp.com/emojis/123456789.png"
    
    # Feature icons
    TICKET_ICON = "https://cdn.discordapp.com/emojis/123456789.png"
    WELCOME_ICON = "https://cdn.discordapp.com/emojis/123456789.png"
    MODERATION_ICON = "https://cdn.discordapp.com/emojis/123456789.png"
    
    @staticmethod
    def get_status_icon(status: str) -> str:
        """Get icon URL for a status"""
        status_map = {
            "online": Icons.ONLINE,
            "idle": Icons.IDLE,
            "dnd": Icons.DND,
            "offline": Icons.OFFLINE
        }
        return status_map.get(status.lower(), Icons.DEFAULT_AVATAR)


class EmbedTemplates:
    """Pre-made embed templates with emotes"""
    
    @staticmethod
    def success(title: str, description: str):
        """Success embed template"""
        import discord
        return discord.Embed(
            title=f"{Emotes.SUCCESS} {title}",
            description=description,
            color=discord.Color.green()
        )
    
    @staticmethod
    def error(title: str, description: str):
        """Error embed template"""
        import discord
        return discord.Embed(
            title=f"{Emotes.ERROR} {title}",
            description=description,
            color=discord.Color.red()
        )
    
    @staticmethod
    def info(title: str, description: str):
        """Info embed template"""
        import discord
        return discord.Embed(
            title=f"{Emotes.INFO} {title}",
            description=description,
            color=discord.Color.blue()
        )
    
    @staticmethod
    def warning(title: str, description: str):
        """Warning embed template"""
        import discord
        return discord.Embed(
            title=f"{Emotes.WARNING} {title}",
            description=description,
            color=discord.Color.orange()
        )


# Helper function to parse custom emotes
def parse_emote(emote_string: str) -> dict:
    """
    Parse emote string and return emote info
    
    Args:
        emote_string: Format "<:name:id>" or "<a:name:id>"
    
    Returns:
        dict with 'animated', 'name', 'id'
    """
    if not emote_string.startswith('<'):
        return {'animated': False, 'name': emote_string, 'id': None}
    
    parts = emote_string.strip('<>').split(':')
    return {
        'animated': parts[0] == 'a',
        'name': parts[1] if len(parts) > 1 else '',
        'id': parts[2] if len(parts) > 2 else None
    }


# Quick access dictionary for common emote combinations
EMOTE_COMBINATIONS = {
    "success": f"{Emotes.SUCCESS} Success!",
    "error": f"{Emotes.ERROR} Error!",
    "loading": f"{Emotes.LOADING} Loading...",
    "ticket_created": f"{Emotes.TICKET} Ticket created!",
    "ticket_closed": f"{Emotes.TICKET_CLOSED} Ticket closed!",
    "welcome_member": f"{Emotes.WAVE} Welcome!",
    "goodbye_member": f"{Emotes.GOODBYE} Goodbye!",
}