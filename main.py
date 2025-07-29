# ==================== IMPORTS ====================
import discord
from discord.ext import commands, tasks
import asyncio
import platform
from riotwatcher import LolWatcher, RiotWatcher
import requests

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ==================== CONFIGURATION ==================== \ 
REGION = 'br1'                       # Your server region
ROUTING_VALUE = 'americas'           # Routing value for account API
CHANNEL_ID = 1396168023509045289       # Discord channel ID where messages will be sent

# ==================== INITIALIZE OBJECTS ====================
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
lol_watcher = LolWatcher(RIOT_API_KEY)
riot_watcher = RiotWatcher(RIOT_API_KEY)

@bot.command(name='profile')
async def profile(ctx, *, args):
    try:
        # Get account using Riot ID
        message = args.split('#')
        id_name = message[0]
        id_tag = message[1]
        account = riot_watcher.account.by_riot_id(ROUTING_VALUE, id_name, id_tag)
        if not account:
            embed = discord.Embed(title="Summoner not found!",color=0x00ff00)

        # Get summoner data using PUUID
        summoner = lol_watcher.summoner.by_puuid(REGION, account['puuid'])
        print(f"Summoner: {lol_watcher.league}")

        # Get champion mastery information
        champion_masteries = lol_watcher.champion_mastery.by_puuid(REGION, account['puuid'])
        top_masterie = champion_masteries[0]

        versions = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()
        latest_version = versions[0]

        # Get champion data
        champion_data = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json").json()
        champion_data = champion_data['data']
        mastery_champion_name = ""
        
        for champion in champion_data.values():
            if champion["key"] == str(top_masterie["championId"]):
                mastery_champion_name = champion["name"]
        formatted_points = f"{top_masterie["championPoints"]:,}"
        mastery_text = f"{mastery_champion_name} - Level {top_masterie["championLevel"]} ({formatted_points} points)"
        # mastery_champion_icon = 

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
        embed.set_thumbnail(url=profile_icon_url)
        embed.add_field(name="Level", value=summoner['summonerLevel'], inline=True)
        embed.add_field(name="Rank", value=rank_text, inline=True)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="🏆 Top Champion Masterie", value="", inline=False)
        embed.add_field(name="", value=mastery_text, inline=False)

        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN, reconnect=True)  # Add reconnect=True
    except discord.errors.LoginFailure:
        print("❌ Invalid Discord bot token")
    except Exception as e:
        print(f"Bot crashed: {e}")