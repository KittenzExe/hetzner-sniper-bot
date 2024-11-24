import nextcord
from nextcord.ext import commands, tasks
from database import setup_database, get_server_count, store_data_in_live_db, update_servers_db, check_for_snipes
from commands import register_commands
import requests
import json

# Create an instance of a bot
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Database setup
setup_database()

# Event handler when the bot is ready
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    check_json_data.start()

# Register commands
register_commands(bot)

# Function to fetch JSON data and modify prices
def fetch_json_data(url):
    response = requests.get(url)
    data = response.json()
    for server in data.get("server", []):
        server["price"] *= 1.234
        server["setup_price"] *= 1.234
        server["hourly_price"] *= 1.234
    return data

# Function to fetch CPU stats from a local JSON file
def fetch_cpu_stats(cpu_name):
    with open('./cpus.json', 'r') as file:
        cpu_stats = json.load(file)
        for cpu in cpu_stats:
            if cpu["name"] == cpu_name:
                return cpu
    return None

# Slash command to define criteria
@bot.slash_command(name="criteria", description="Set criteria for snipes")
async def set_criteria(interaction: nextcord.Interaction, cpu_cores: int, ram_size: int):
    user_id = interaction.user.id
    criteria = {
        "cpu_cores": cpu_cores,
        "ram_size": ram_size
    }
    with open(f'criteria_{user_id}.json', 'w') as file:
        json.dump(criteria, file)
    await interaction.response.send_message(f"Criteria set: CPU Cores = {cpu_cores}, RAM Size = {ram_size} GB")

# Task to check JSON data every 10 seconds
@tasks.loop(seconds=10)
async def check_json_data():
    url = "https://www.hetzner.com/public/_resources/app/jsondata/live_data_sb.json"
    channel_id = 1291033002272493640  # Replace with your channel ID
    snipe_channel_id = 1291106419529220218  # Replace with your snipe channel ID

    try:
        new_data = fetch_json_data(url)
        print("Fetched JSON data")
        store_data_in_live_db(new_data)
        print("Stored JSON data in live database")
        current_server_count = get_server_count()
        print(f"Current server count: {current_server_count}")
        update_servers_db()
        print("Updated servers database")
        new_server_count = get_server_count()
        print(f"New server count: {new_server_count}")

        if new_server_count != current_server_count:
            new_entries = check_for_snipes()
            print(f"New entries: {new_entries}")
            channel = bot.get_channel(channel_id)
            snipe_channel = bot.get_channel(snipe_channel_id)
            if channel:
                await channel.send(f"Server data has been updated. Total servers: {new_server_count}")
            if snipe_channel:
                for user_id, server in new_entries:
                    euro_price = server[7]
                    aud_price = euro_price * 1.6  # Conversion rate from Euro to AUD
                    cpu_stats = fetch_cpu_stats(server[1])

                    # Load user criteria
                    try:
                        with open(f'criteria_{user_id}.json', 'r') as file:
                            criteria = json.load(file)
                    except FileNotFoundError:
                        criteria = {"cpu_cores": 0, "ram_size": 0}

                    # Check criteria
                    matches = 0
                    if cpu_stats and cpu_stats["cores"] >= criteria["cpu_cores"]:
                        matches += 1
                    if server[6] >= criteria["ram_size"]:
                        matches += 1

                    # Determine embed color and image
                    if matches == 0:
                        color = nextcord.Color.red()
                        ping_user = False
                        image_path = './images/miss-osaka-scary-stories-slowly-turns-around.gif'
                    elif matches == 1:
                        color = nextcord.Color.yellow()
                        ping_user = False
                        image_path = './images/yuuka.jpg'
                    else:
                        color = nextcord.Color.green()
                        ping_user = True
                        image_path = './images/GXM384hawAAL4ID.jpg'

                    embed = nextcord.Embed(
                        title=f"New Snipe! Server ID: {server[0]}",
                        description="woa, new server!",
                        color=color,
                        url=f"https://www.hetzner.com/sb/#search={server[0]}"
                    )
                    embed.add_field(name="CPU", value=server[1], inline=True)
                    embed.add_field(name="CPU Cores", value=cpu_stats["cores"] if cpu_stats else "N/A", inline=True)
                    embed.add_field(name="CPU Threads", value=cpu_stats["threads"] if cpu_stats else "N/A", inline=True)
                    embed.add_field(name="Base Clock", value=cpu_stats["base_clock"] if cpu_stats else "N/A", inline=True)
                    embed.add_field(name="Max Clock", value=cpu_stats["max_clock"] if cpu_stats else "N/A", inline=True)
                    embed.add_field(name="Traffic", value=server[3], inline=True)
                    embed.add_field(name="Bandwidth", value=server[4], inline=True)
                    embed.add_field(name="RAM", value=server[5], inline=True)
                    embed.add_field(name="RAM Size", value=server[6], inline=True)
                    embed.add_field(name="Price (EUR)/per month", value=f"€{euro_price:.2f}", inline=True)
                    embed.add_field(name="Price (AUD)/per month", value=f"A${aud_price:.2f}", inline=True)
                    embed.add_field(name="Setup Price", value=f"€{server[8]:.2f}", inline=True)
                    embed.add_field(name="Hourly Price", value=f"€{server[9]:.4f}", inline=True)
                    embed.add_field(name="HDD", value=server[10], inline=True)
                    embed.add_field(name="HDD Size", value=server[11], inline=True)
                    embed.add_field(name="HDD Count", value=server[12], inline=True)
                    embed.add_field(name="Datacenter", value=server[13], inline=True)
                    embed.add_field(name="Next Reduce Timestamp", value=server[15], inline=True)

                    # Attach image to embed
                    file = nextcord.File(image_path, filename="image.png")
                    embed.set_image(url="attachment://image.png")

                    if ping_user:
                        await snipe_channel.send(content=f"<@{user_id}>", embed=embed, file=file)
                    else:
                        await snipe_channel.send(embed=embed, file=file)
    except Exception as e:
        print(f"Error fetching or processing JSON data: {e}")

# Start the loop when the bot is ready
@bot.event
async def on_ready():
    check_json_data.start()
    print(f"Logged in as {bot.user}")

# Run the bot with your token
bot.run('YOUR_TOEKEN_HERE')