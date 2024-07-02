import re
import sys
import requests
from datetime import datetime

from rich import print
from rich.table import Table
from rich.console import Console

# if len(sys.argv) < 2:
#     print("Error: debug port is required.")
#     print("USAGE: [cyan]python3 bee_checkup.py <BEE_DEBUG_API_URL>[/cyan]")
#     sys.exit(1)

bee_debug_api_url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else ""
if not bee_debug_api_url:
    bee_debug_api_url = "http://localhost:1635"

def get_bool(b, add_yn=False):
    out = "✅" if b else "❌"
    if add_yn:
        out += " Yes" if b else " No"
    return out


def get_availability_string(item):
    date_string = item["x"].split(".")[0]
    availability = item["y"]
    datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    formatted_date = datetime_obj.strftime("%b %d, %Y %H:%M:%S")
    return f"{get_bool(availability == 1)} - {formatted_date}\n"


def hex_to_group(hex_string, depth):
    # Check for "0x" prefix and remove it if present
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]

    first_two_bytes = hex_string[:4]  # Get the first four characters
    value = int(first_two_bytes, 16)  # Convert it to a decimal number
    group = value // (2 ** (16 - depth))  # Calculate the group based on depth
    return group

console = Console()
latest_bee = requests.get(
    "https://api.github.com/repos/ethersphere/bee/releases/latest"
).json()["tag_name"][1:]

# Fetch rstatus
rstatus_url = f"{bee_debug_api_url}/status"

try:
    rstatus_data = requests.get(rstatus_url).json()
except:
    print(
        f"[red]Error: Could not connect to [cyan]Bee node[/cyan] at [cyan]{bee_debug_api_url}[/cyan].[/red]"
    )
    sys.exit(1)
if "code" in rstatus_data and rstatus_data["code"] == 400 and rstatus_data["message"] == 'operation not supported in dev mode':
    print(
        f"[red]Cannot create report: [cyan]Bee node[/cyan] at [cyan]{bee_debug_api_url}[/cyan] is running in [cyan]dev mode[/cyan].[/red]"
    )
    sys.exit(1)
reserveSize = rstatus_data["reserveSize"]

beeMode = rstatus_data["beeMode"]
pullsyncRate = rstatus_data["pullsyncRate"]
connectedPeers = rstatus_data["connectedPeers"]

# Fetch status/peers 
peers_url = f"{bee_debug_api_url}/status/peers"
peers_data = requests.get(peers_url).json()
neighborhoodSize = peers_data["snapshots"][-1]["neighborhoodSize"]

NA_NFM = "N.A (except in Full Mode)"
# Fetch redistribution state
print(beeMode)
if(beeMode == 'full'):
    redistributionstate_url = f"{bee_debug_api_url}/redistributionstate"
    redistributionstate_data = requests.get(redistributionstate_url).json()
    hasSufficientFunds = redistributionstate_data["hasSufficientFunds"]
    isFullySynced = redistributionstate_data["isFullySynced"]
    isFrozen = redistributionstate_data["isFrozen"]
    lastPlayedRound = redistributionstate_data["lastPlayedRound"]
    current_round = redistributionstate_data["round"]
    phase = redistributionstate_data["phase"]
    lastWonRound = redistributionstate_data["lastWonRound"]
    lastFrozenRound = redistributionstate_data["lastFrozenRound"]
    lastSelectedRound = redistributionstate_data["lastSelectedRound"]
    lastSampleDuration = redistributionstate_data["lastSampleDuration"]
    block = redistributionstate_data["block"]
    reward = redistributionstate_data["reward"]
else:
    hasSufficientFunds = NA_NFM
    isFullySynced = NA_NFM
    isFrozen = ""
    lastPlayedRound = 0
    current_round = NA_NFM
    phase = NA_NFM
    lastWonRound = 0
    lastFrozenRound = 0
    lastSelectedRound = 0
    lastSampleDuration = 0
    block = NA_NFM
    reward = NA_NFM
# Fetch topology
topology_url = f"{bee_debug_api_url}/topology"
topology_data = requests.get(topology_url).json()
depth = topology_data["depth"]
reachability = topology_data["reachability"]

# Fetch stake
stake_url = f"{bee_debug_api_url}/stake"
stake_data = requests.get(stake_url).json()
stakedAmount = float(stake_data["stakedAmount"]) / 10**16

# Fetch reservestate
reservestate_url = f"{bee_debug_api_url}/reservestate"
reservestate_data = requests.get(reservestate_url).json()
print(reservestate_data)
radius = reservestate_data["radius"]
storageRadius = reservestate_data["storageRadius"]

# Fetch wallet
wallet_url = f"{bee_debug_api_url}/wallet"
wallet_data = requests.get(wallet_url).json()
bzzBalance = round((float(wallet_data["bzzBalance"]) / 10**16), 2)
nativeTokenBalance = round((float(wallet_data["nativeTokenBalance"]) / 10**18), 2)
walletAddress = wallet_data["walletAddress"]

# Fetch health
health_url = f"{bee_debug_api_url}/health"
health_data = requests.get(health_url).json()
version = health_data["version"].split("-")[0]
status = health_data["status"]

# Fetch addresses
addresses_url = f"{bee_debug_api_url}/addresses"
addresses_data = requests.get(addresses_url).json()
overlay = addresses_data["overlay"]

# fetch swarmscan data for the node
swarmscan_data = requests.get(f"https://swarmscan.io/i/network/nodes/{overlay}").json()
swarmscan_neighborhoods = requests.get("https://swarmscan.io/i/network/neighborhoods").json()
network_depth = swarmscan_neighborhoods["depth"]
neighborhood_count = swarmscan_neighborhoods["neighborhoodCount"]
nbhood = hex_to_group(overlay, network_depth)

hint = {
    "[cyan]NODE[/cyan]": "",
    "Wallet": f"🔗 [cyan][link=https://gnosisscan.io/address/{walletAddress}]Gnosisscan Link[/link][/cyan]",
    "Overlay": f"🔗 [cyan][link=https://swarmscan.io/nodes/{overlay}]Swarmscan Link - Node[/link][/cyan]",
    "Neighborhood": "🔗 [cyan][link=https://swarmscan.io/neighborhoods]Swarmscan Link - Neighborhoods[/link][/cyan]",
    "Version": " " if version == latest_bee else f"[magenta]{latest_bee} is available[/magenta]",
    "Bee Mode": "🔗 [cyan][link=https://docs.ethswarm.org/docs/bee/installation/install#full-nodes]Full, Light & Ultralight mode[/link][/cyan]",
    "Connected Peers": "".join([
        "🟦 Should be [magenta]150+[/magenta] peers",
        " 🔗 [cyan][link=https://docs.ethswarm.org/docs/learn/faq#what-determines-the-number-of-peers-and-how-to-influence-their-number-why-are-there-sometimes-300-peers-and-sometimes-30]Connected Peers[/link][/cyan]",
        " | [cyan][link=https://docs.ethswarm.org/docs/learn/faq#connectivity]Connectivity[/link][/cyan]"
        ]),
    "Pullsync Rate": '🔗 [cyan][link=https://docs.ethswarm.org/docs/learn/technology/disc#push-sync-pull-sync-and-retrieval-protocols]Pull Sync[/link][/cyan]',
    "Status": "",
    "Has Sufficient Funds": "🔗 [cyan][link=https://docs.ethswarm.org/docs/bee/installation/fund-your-node]Fund Your Node[/link][/cyan]",
    "Is Fully Synced": "🟦 Takes a [magenta]few hours upto a day[/magenta] upon startup",
    "Not Frozen": "".join([
        "🟦 Freeze duration depends on the current depth",
        f" | [magenta]~ { round((152 * (2 ** depth)*5)/(60*60*24))} days[/magenta] at depth [magenta]{depth}[/magenta]",
        " 🔗 [cyan][link=https://docs.ethswarm.org/docs/learn/technology/incentives#penalties]Penalties[/link][/cyan]",
    ]),
    "Reachable": "🔗 [cyan][link=https://docs.ethswarm.org/docs/bee/installation/connectivity]Connectivity[/link][/cyan]",
    "Depth": "🔗 [cyan][link=https://docs.ethswarm.org/docs/learn/glossary#2-area-of-responsibility-related-depths]Depth[/link][/cyan]",
    "Storage Radius": f"🟦 Should be [magenta]{network_depth}[/magenta]",
    "Staked Amount": "".join([
        "🔗 [cyan][link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking]Staking[/link][/cyan]",
        " | [cyan][link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking#maximizing-staking-rewards]Maximizing Staking Rewards[/link][/cyan]",
    ]),
    "xDAI": "".join([
        "🟦 Minimum [magenta]0.1 xDAI[/magenta] recommended",
        " 🔗 [cyan][link=https://docs.ethswarm.org/docs/bee/installation/fund-your-node]Fund Your Node[/link][/cyan]",
        " | [cyan][link=https://docs.ethswarm.org/docs/learn/tokens#xdai]xDAI[/link][/cyan]",
    ]),
    "xBZZ": "".join([
        "🟦 Minimum [magenta]1 xBZZ[/magenta] recommended ",
        "🔗 [cyan][link=https://docs.ethswarm.org/docs/bee/installation/fund-your-node]Fund Your Node[/link][/cyan]",
        " | [cyan][link=https://docs.ethswarm.org/docs/learn/tokens#xbzz]xBZZ[/link][/cyan]",
    ]),
    "Neighborhood Size": " | ".join([
        # "Typically more than [magenta]4[/magenta] nodes",
        "🔗 [cyan][link=https://docs.ethswarm.org/docs/learn/technology/disc#neighborhoods]Neighborhoods[/link][/cyan]",
        "[cyan][link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking#neighborhood-selection]Neighborhood Selection[/link][/cyan]",
        "[cyan][link=https://docs.ethswarm.org/docs/bee/installation/install#set-target-neighborhood-optional]Set Target Neighborhood[/link][/cyan]",
        "[cyan][link=https://swarmscan.io/neighborhoods]Swarmscan[/link][/cyan]",
    ]),
    "Reserve Size": "",
    "[cyan]LOTTERY[/cyan]": "",
    "Current Round": "🔗 [cyan][link=https://docs.ethswarm.org/docs/learn/technology/incentives#storage-incentives-details]Storage Incentives[/link][/cyan]",
    "Playing Current Round": "",
    "Last Won Round": '',
    "Last Frozen Round": '',
    "Last Selected Round": '',
    "Last Sample Duration": '',
    "Rewards Collected": "",
}

row = {
    "[cyan]NODE[/cyan]": "",
    "Wallet": f"{walletAddress[2:5]}...{walletAddress[-3:]}",
    "Overlay": f"{overlay[0:3]}...{overlay[-3:]}",
    "Neighborhood": f"{bin(nbhood)[2:].rjust(network_depth,'0')} (#{nbhood}/{neighborhood_count})",
    "Version": f"✅ {version}" if version == latest_bee else f"🟡 {version}",
    "Bee Mode": f"✅ {beeMode}" if beeMode == "full" else f"🟡 {beeMode}",
    "Connected Peers": f"✅ {connectedPeers}" if connectedPeers > 149 else f"🟡 {connectedPeers}",
    "Pullsync Rate": f"✅ 0 (Synced)" if pullsyncRate == 0 else f"🟡 {pullsyncRate} (Syncing)",
    "Status": f"{get_bool(status == 'ok')} {status}",
    "Has Sufficient Funds": get_bool(hasSufficientFunds, True),
    "Is Fully Synced": get_bool(isFullySynced, True),
    "Not Frozen": get_bool(isFrozen == False, True) if beeMode == 'full' else "✅",
    "Reachable": get_bool(reachability, True),
    "Depth": f"✅ {depth}" if depth == network_depth else f"🟡 {depth}",
    "Storage Radius": f"✅ {storageRadius}" if storageRadius == network_depth else f"🟡 {storageRadius}" if beeMode == 'full' else NA_NFM,
    "Staked Amount": f"✅ {stakedAmount} xBZZ" if stakedAmount >= 10 else f"🟡 {stakedAmount} BZZ" if beeMode == 'full' else NA_NFM,
    "xDAI": f"✅ {nativeTokenBalance} xDAI" if nativeTokenBalance >= 0.1 else f"🟡 {nativeTokenBalance} xDAI",
    "xBZZ": f"✅ {bzzBalance} xBZZ" if bzzBalance >= 1 else f"🟡 {bzzBalance} xBZZ",
    "Neighborhood Size": neighborhoodSize,
    "Reserve Size": f"{(reserveSize * 4) / 1000 / 1000 :.3f} GB ({reserveSize} chunks)",
    "[cyan]LOTTERY[/cyan]": "",
    "Current Round": current_round,
    "Playing Current Round": ("🟡 Yes" if lastPlayedRound == current_round else "No") if beeMode == 'full' else NA_NFM,
    "Last Won Round": f"{'Not Yet' if lastWonRound == 0 else current_round - lastWonRound}{'' if lastWonRound == 0 else ' rounds ago'} ({lastWonRound})"  if beeMode == 'full' else NA_NFM,
    "Last Frozen Round": f"{'Not Yet' if lastFrozenRound == 0 else current_round - lastFrozenRound}{'' if lastFrozenRound == 0 else ' rounds ago'} ({lastFrozenRound})" if beeMode == 'full' else NA_NFM,
    "Last Selected Round": f"{'Not Yet' if lastSelectedRound == 0 else current_round - lastSelectedRound}{'' if lastSelectedRound == 0 else ' rounds ago'} ({lastSelectedRound})" if beeMode == 'full' else NA_NFM,
    "Last Sample Duration": f"{lastSampleDuration / 60000000000:.1f} minutes"  if lastSampleDuration > 0  else "Not Yet (0)" if beeMode == 'full' else NA_NFM,
    "Rewards Collected": f"{format(float(reward) / 1e16, '.2f')} BZZ" if beeMode == 'full' else NA_NFM,
}

table = Table(show_header=True, header_style="bold magenta")

table.add_column("Section")
table.add_column("Key")
table.add_column("Value")
table.add_column("Additional Info")

for key, value in row.items():
    if value == "":
        table.add_section()
        table.add_row(key)
    else:
        table.add_row("", key, str(value), str(hint[key]))

availability_data =  [] if "code" in swarmscan_data and swarmscan_data["code"] == 404 else swarmscan_data["availabilityChart"]
availability_string = ""

for item in availability_data[:4]:
    availability_string += get_availability_string(item)

if availability_data.__len__() > 4:
    availability_string += "...\n"
    availability_string += get_availability_string(availability_data[-1])

table.add_section()
table.add_row(
    "[cyan]AVAILABILITY[/cyan]", "", 
    "\n" + availability_string.strip(), 
    f"🔗 [cyan][link=https://swarmscan.io/nodes/{overlay}]Swarmscan Link - Node[/link][/cyan]",
)
table.add_section()
rgx = r':\d+' # regex to match port number in url
table.add_row(
    "[cyan]PERFORMANCE[/cyan]", NA_NFM, NA_NFM,
    "\n".join([
        "🔗 [cyan][link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking#check-node-performance]Check Node Performance[/link][/cyan]",
        "To check hardware performance, run:",
        f"> [yellow]curl -X GET { bee_debug_api_url }/rchash/{network_depth}/aaaa/aaaa | jq[/yellow]",
        "In the JSON response, the value of [magenta]Duration[/magenta] should be less than [magenta]6[/magenta] minutes ([magenta]360000000000[/magenta] nanoseconds).",
    ]),
)
console.print(table)
