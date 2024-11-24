import nextcord
from nextcord.ext import commands
from database import get_server_by_id, get_servers_by_criteria, insert_snipe

def register_commands(bot):
    # Define a slash command to say hello
    @bot.slash_command(name="hello", description="Say hello!")
    async def hello(interaction: nextcord.Interaction):
        await interaction.response.send_message("Hello!")

    # Define a slash command to lookup server details
    @bot.slash_command(name="lookup", description="Lookup server details by ID")
    async def lookup(interaction: nextcord.Interaction, server_id: int):
        server = get_server_by_id(server_id)
        if server:
            euro_price = server[7]
            aud_price = euro_price * 1.6  # Conversion rate from Euro to AUD

            embed = nextcord.Embed(title=f"Server ID: {server[0]}", description=server[1])
            embed.add_field(name="CPU", value=server[1], inline=False)
            embed.add_field(name="CPU Count", value=server[2], inline=False)
            embed.add_field(name="Traffic", value=server[3], inline=False)
            embed.add_field(name="Bandwidth", value=server[4], inline=False)
            embed.add_field(name="RAM", value=server[5], inline=False)
            embed.add_field(name="RAM Size", value=server[6], inline=False)
            embed.add_field(name="Price (EUR)/per month", value=f"€{euro_price:.2f}", inline=False)
            embed.add_field(name="Price (AUD)/per month", value=f"A${aud_price:.2f}", inline=False)
            embed.add_field(name="Setup Price", value=f"€{server[8]:.2f}", inline=False)
            embed.add_field(name="Hourly Price", value=f"€{server[9]:.4f}", inline=False)
            embed.add_field(name="HDD", value=server[10], inline=False)
            embed.add_field(name="HDD Size", value=server[11], inline=False)
            embed.add_field(name="HDD Count", value=server[12], inline=False)
            embed.add_field(name="Datacenter", value=server[13], inline=False)
            embed.add_field(name="Specials", value=server[14], inline=False)
            embed.add_field(name="Next Reduce Timestamp", value=server[15], inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No server found with ID {server_id}")

    # Define a slash command to get servers based on criteria
    @bot.slash_command(name="get", description="Get servers based on criteria (e.g., /get cpu=Intel ram_size=32 price=20-50)")
    async def get_servers(interaction: nextcord.Interaction, criteria: str):
        matching_servers = get_servers_by_criteria(criteria)
        if matching_servers:
            embed = nextcord.Embed(title="Matching Servers", description="List of server IDs that match the criteria")
            embed.add_field(name="Server IDs", value=", ".join(map(lambda x: str(x[0]), matching_servers)), inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No servers match the given criteria")

    # Define a slash command to set up snipes
    @bot.slash_command(name="snipe", description="Set up a snipe with a min and max price")
    async def snipe(interaction: nextcord.Interaction, min_price: float, max_price: float):
        await interaction.response.defer()  # Defer the response
        user_id = interaction.user.id
        insert_snipe(user_id, min_price, max_price)
        await interaction.followup.send(f"Snipe set up for prices between €{min_price:.2f} and €{max_price:.2f}")