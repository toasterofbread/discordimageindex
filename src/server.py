import disnake as discord
from disnake.abc import GuildChannel
from disnake.ext import commands

DISCORD_CHANNEL_HYPHEN_KEY = "hyphen"

class Server(commands.Bot):
    def __init__(self, bot_token: str, images_channel_category: str, images_channel_prefix: str):
        intents = discord.Intents.default()
        intents.message_content = True
        
        _super = super()
        _super.__init__(intents = intents)

        self.bot_token = bot_token
        self.images_channel_category = images_channel_category
        self.images_channel_prefix = images_channel_prefix

        def event(name: str | None = None):
            def decorator(function):
                if name is not None:
                    function.__name__ = name
                return _super.event(function)
            return decorator
        self.event_wrapper = event

        @event("on_ready")
        async def onReady():
            print("Bot is ready!")
            await self.onReady()

    def runServer(self):
        self.run(self.bot_token)

    async def onReady(self):
        pass

    def fetchIndexChannels(self) -> dict[str, GuildChannel]:
        category: GuildChannel = self.get_channel(int(self.images_channel_category))
        channels = {}

        for channel in category.channels:
            if channel is None or not channel.name.startswith(self.images_channel_prefix):
                continue
            
            index = channel.name[len(self.images_channel_prefix):]
            if index == DISCORD_CHANNEL_HYPHEN_KEY:
                index = "-"

            channels[index] = channel
        
        return channels
    
    async def fetchChannelImages(self, channel: GuildChannel, index: str) -> dict[str, str]:
        messages = await channel.history(limit = 10000).flatten()
        images = {}

        for message in messages:
            if message.author != self.user:
                continue
            if not message.content[0].lower() == index.lower():
                continue
            if len(message.attachments) == 0:
                continue

            images[message.content] = message.attachments[0].url

        return images
