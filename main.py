# ==================== IMPORTS ====================
import discord
from discord.ext import commands, tasks
import asyncio
from riotwatcher import LolWatcher, RiotWatcher, ApiError
import json
import os
from datetime import datetime, timezone

# ==================== CONFIGURATION ====================
# These are your personal keys and settings - replace with real values

RIOT_ID_NAME = 'Lightbeal3'           # Your Riot ID name (the part before #)
RIOT_ID_TAG = 'BR1'                  # Your Riot ID tag (the part after #) - usually BR1 for Brazil
REGION = 'br1'                       # Your server region (lowercase)
ROUTING_VALUE = 'americas'           # Routing value for account API (americas for Brazil)
CHANNEL_ID = 1396168023509045289       # Discord channel ID where messages will be sent

# ==================== INITIALIZE OBJECTS ====================
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
lol_watcher = LolWatcher(RIOT_API_KEY)
riot_watcher = RiotWatcher(RIOT_API_KEY)
last_match_file = 'last_match.json'

def load_last_match():
    try:
        with open(last_match_file, 'r') as f:
            data = json.load(f)
            return data.get('last_match_id')
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print("Warning: last_match.json is corrupted, starting fresh")
        return None

def save_last_match(match_id):
    try:
        with open(last_match_file, 'w') as f:
            json.dump({'last_match_id': match_id}, f)
        print(f"Saved last match ID: {match_id}")
    except Exception as e:
        print(f"Error saving last match ID: {e}")

def format_match_result(match_data, summoner_puuid):
    # Find our summoner's data among all 10 participants
    participant = None
    for p in match_data['info']['participants']:
        if p['puuid'] == summoner_puuid:
            participant = p
            break
    
    if not participant:
        return None
    
    # Extract match information
    game_mode = match_data['info']['gameMode']          
    game_duration = match_data['info']['gameDuration']  
    win = participant['win']                            
    champion = participant['championName']              
    kills = participant['kills']
    deaths = participant['deaths']
    assists = participant['assists']

    duration_minutes = game_duration // 60
    duration_seconds = game_duration % 60

    if win:
        result_text = "🏆 **VICTORY**"
        embed_color = 0x00ff00  # Green in hexadecimal
    else:
        result_text = "💀 **DEFEAT**"
        embed_color = 0xff0000  # Red in hexadecimal

    # Create Discord embed
    embed = discord.Embed(
        title=result_text,
        color=embed_color,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Champion", value=champion, inline=True)
    embed.add_field(name="KDA", value=f"{kills}/{deaths}/{assists}", inline=True)
    embed.add_field(name="Game Mode", value=game_mode, inline=True)
    embed.add_field(name="Duration", value=f"{duration_minutes}m {duration_seconds}s", inline=True)
    
    return embed

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in to Discord!')
    if not check_matches.is_running():
        check_matches.start()

@bot.event
async def on_message(message):
    print(message)
    print(f"Message received: '{message.content}' from {message.author} in {message.channel}")
    
    # Don't respond to bot messages
    if message.author == bot.user:
        return
    
    # This is crucial - process commands
    await bot.process_commands(message)

@tasks.loop(minutes=2)  
async def check_matches():
    try:
        print(f"Checking for new matches at {datetime.now()}")
        
        # Get account data using Riot ID (new method)
        account = riot_watcher.account.by_riot_id(ROUTING_VALUE, RIOT_ID_NAME, RIOT_ID_TAG)
        summoner_puuid = account['puuid']
        summoner = lol_watcher.summoner.by_puuid(REGION, account['puuid'])
        print(summoner)
        # Get match list using PUUID
        matches = lol_watcher.match.matchlist_by_puuid(ROUTING_VALUE, summoner_puuid, count=10)
        print(matches)

        if not matches:
            print("No matches found")
            return

        latest_match_id = matches[0]
        last_match_id = load_last_match()

        if latest_match_id != last_match_id:
            print("New match detected!")
            match_data = lol_watcher.match.by_id(ROUTING_VALUE, latest_match_id)
            # print(f"Dados da partida: {match_data}")
            if match_data['info']['gameEndTimestamp'] > 0:
                # Match is finished, send notification
                embed = format_match_result(match_data, summoner_puuid)
                
                if embed:
                    channel = bot.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.send(embed=embed)
                        print("Match result sent to Discord!")
                    else:
                        print(f"Channel with ID {CHANNEL_ID} not found")
                
                # Save the new match ID
                save_last_match(latest_match_id)
            else:
                print("Match is still ongoing")
        else:
            print("No new matches")

    except ApiError as err:
        if err.response.status_code == 429:
            print("Rate limit exceeded. Waiting...")
            await asyncio.sleep(60)
        elif err.response.status_code == 404:
            print("Account/Summoner not found - check your Riot ID")
        else:
            print(f"API Error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")

@bot.command(name='status')
async def status(ctx):
    try:
        print("Li o comando!")
        # Get account using Riot ID
        account = riot_watcher.account.by_riot_id(ROUTING_VALUE, RIOT_ID_NAME, RIOT_ID_TAG)
        
        # Get summoner data using PUUID
        summoner = lol_watcher.summoner.by_puuid(REGION, account['puuid'])
        
        embed = discord.Embed(title="🤖 Bot Status", color=0x00ff00)
        embed.add_field(name="Riot ID", value=f"{RIOT_ID_NAME}#{RIOT_ID_TAG}", inline=True)
        embed.add_field(name="Region", value=REGION.upper(), inline=True)
        embed.add_field(name="Level", value=summoner['summonerLevel'], inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("❌ Invalid Discord bot token")