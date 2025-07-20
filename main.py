# ==================== IMPORTS ====================
import discord
from discord.ext import commands, tasks
import asyncio
import platform
from riotwatcher import LolWatcher, RiotWatcher, ApiError
import json
import os
from datetime import datetime, timezone

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ==================== CONFIGURATION ====================
REGION = 'br1'                       # Your server region
ROUTING_VALUE = 'americas'           # Routing value for account API
CHANNEL_ID = 1396168023509045289       # Discord channel ID where messages will be sent

# ==================== INITIALIZE OBJECTS ====================
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
lol_watcher = LolWatcher(RIOT_API_KEY)
riot_watcher = RiotWatcher(RIOT_API_KEY)

@bot.event
async def on_message(message):
    print(message)
    print(f"Message received: '{message.content}' from {message.author} in {message.channel}")
    
    # Don't respond to bot messages
    if message.author == bot.user:
        return
    
    # Debug: Check if we can access message content
    try:
        content = getattr(message, 'content', None)
        print(f"Message from {message.author}: '{content}'")

        # Only process messages that start with !
        if content and content.startswith('!'):
            print(f"Processing command: {content}")
            # Process the command
            await bot.process_commands(message)
        else:
            print("Message doesn't start with ! - ignoring")
            
    except Exception as e:
        print(f"Error processing message: {e}")

@bot.command(name='profile')
async def profile(ctx, *, args):
    try:
        # Get account using Riot ID
        # print(args)
        message = args.split('#')
        id_name = message[0]
        id_tag = message[1]
        account = riot_watcher.account.by_riot_id(ROUTING_VALUE, id_name, id_tag)
        if not account:
            embed = discord.Embed(title="Summoner not found!",color=0x00ff00)

        # Get summoner data using PUUID
        summoner = lol_watcher.summoner.by_puuid(REGION, account['puuid'])
        print(f"Summoner: {lol_watcher.league}")

        # Get ranked information
        ranked_stats = lol_watcher.league.by_puuid(REGION, account['puuid'])
        print(f"ranked stats: {ranked_stats}")
        
        # Find Solo/Duo rank 
        solo_rank = None
        for queue in ranked_stats:
            if queue['queueType'] == 'RANKED_SOLO_5x5':
                solo_rank = queue
                break
        
        # Format rank information
        if solo_rank:
            tier = solo_rank['tier'].capitalize()
            rank = solo_rank['rank']
            lp = solo_rank['leaguePoints']
            rank_text = f"{tier} {rank} ({lp} LP)"
        else:
            rank_text = "Unranked"

        account_name = value=f"{account["gameName"]}#{account["tagLine"]}"
        profile_icon_id = summoner["profileIconId"]
        profile_icon_url = f"https://ddragon.leagueoflegends.com/cdn/14.24.1/img/profileicon/{profile_icon_id}.png"

        embed = discord.Embed(color=0x00ff00)
        # embed = discord.Embed(title=f"Level: {summoner['summonerLevel']}", color=0x00ff00)
        embed.set_author(name=account_name, icon_url=profile_icon_url)
        # embed.set_image(url=profile_icon_url)
        embed.add_field(name="Level", value=summoner['summonerLevel'], inline=True)
        embed.add_field(name="Rank", value=rank_text, inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.event
async def on_disconnect():
    print("Bot disconnected from Discord")

@bot.event
async def on_resumed():
    print("Bot connection resumed")

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN, reconnect=True)  # Add reconnect=True
    except discord.errors.LoginFailure:
        print("❌ Invalid Discord bot token")
    except Exception as e:
        print(f"Bot crashed: {e}")