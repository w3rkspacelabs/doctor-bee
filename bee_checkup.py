import sys
import requests
from rich.console import Console
from rich.table import Table
from rich import print
from datetime import datetime

if len(sys.argv) < 2:
    print("Error: debug port is required.")
    print("USAGE: [cyan]python3 bee_checkup.py <BEE_DEBUG_PORT>[/cyan]")
    sys.exit(1)

port = sys.argv[1]

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

def process_overlay(overlay, depth):
    group = hex_to_group(overlay, depth)
    return group

console = Console()
latest_bee = requests.get(
    "https://api.github.com/repos/ethersphere/bee/releases/latest"
).json()["tag_name"][1:]

# Fetch rstatus
rstatus_url = f"http://localhost:{port}/status"

try:
    rstatus_data = requests.get(rstatus_url).json()
except:
    print(
        f"[red]Error: Could not connect to [cyan]Bee node[/cyan] at debug port [cyan]{port}[/cyan].[/red]"
    )
    sys.exit(1)

reserveSize = rstatus_data["reserveSize"]
neighborhoodSize = rstatus_data["neighborhoodSize"]
beeMode = rstatus_data["beeMode"]
pullsyncRate = rstatus_data["pullsyncRate"]
connectedPeers = rstatus_data["connectedPeers"]

# Fetch redistribution state
redistributionstate_url = f"http://localhost:{port}/redistributionstate"
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

# Fetch topology
topology_url = f"http://localhost:{port}/topology"
topology_data = requests.get(topology_url).json()
depth = topology_data["depth"]
reachability = topology_data["reachability"]

# Fetch stake
stake_url = f"http://localhost:{port}/stake"
stake_data = requests.get(stake_url).json()
stakedAmount = float(stake_data["stakedAmount"]) / 10**16

# Fetch reservestate
reservestate_url = f"http://localhost:{port}/reservestate"
reservestate_data = requests.get(reservestate_url).json()
radius = reservestate_data["radius"]
storageRadius = reservestate_data["storageRadius"]

# Fetch wallet
wallet_url = f"http://localhost:{port}/wallet"
wallet_data = requests.get(wallet_url).json()
bzzBalance = round((float(wallet_data["bzzBalance"]) / 10**16), 2)
nativeTokenBalance = round((float(wallet_data["nativeTokenBalance"]) / 10**18), 2)
walletAddress = wallet_data["walletAddress"]

# Fetch health
health_url = f"http://localhost:{port}/health"
health_data = requests.get(health_url).json()
version = health_data["version"].split("-")[0]
status = health_data["status"]

# Fetch addresses
addresses_url = f"http://localhost:{port}/addresses"
addresses_data = requests.get(addresses_url).json()
overlay = addresses_data["overlay"]

# fetch swarmscan data for the node
swarmscan_data = requests.get(f"https://swarmscan.io/i/network/nodes/{overlay}").json()
swarmscan_neighborhoods = requests.get("https://swarmscan.io/i/network/neighborhoods").json()
network_depth = swarmscan_neighborhoods["depth"]
neighborhood_count = swarmscan_neighborhoods["neighborhoodCount"]
nbhood = hex_to_group(overlay, depth)

hint = {
    "[cyan]NODE[/cyan]": "",
    "Wallet": f"🔗 [link=https://gnosisscan.io/address/{walletAddress}]Gnosisscan Link[/link]",
    "Overlay": f"🔗 [link=https://swarmscan.io/nodes/{overlay}]Swarmscan Link[/link] - Node",
    "Neighborhood": "🔗 [link=https://swarmscan.io/neighborhoods]Swarmscan Link[/link] - Neighborhoods",
    "Version": " " if version == latest_bee else f"[yellow]{latest_bee} is available[/yellow]",
    "Bee Mode": "🔗 [link=https://docs.ethswarm.org/docs/bee/installation/install#full-nodes]Full, Light & Ultralight mode[/link]",
    "Connected Peers": "".join([
        "🛈 Should be [yellow]150+[/yellow] peers",
        " 🔗 [link=https://docs.ethswarm.org/docs/learn/faq#what-determines-the-number-of-peers-and-how-to-influence-their-number-why-are-there-sometimes-300-peers-and-sometimes-30]Connected Peers[/link]",
        " | [link=https://docs.ethswarm.org/docs/learn/faq#connectivity]Connectivity[/link]"
        ]),
    "Pullsync Rate": '🔗 [link=https://docs.ethswarm.org/docs/learn/technology/disc#push-sync-pull-sync-and-retrieval-protocols]Pull Sync[/link]',
    "Status": "",
    "Has Sufficient Funds": "🔗 [link=https://docs.ethswarm.org/docs/bee/installation/fund-your-node]Fund Your Node[/link]",
    "Is Fully Synced": "🛈 Takes a [yellow]few hours upto a day[/yellow] upon startup",
    "Not Frozen": "".join([
        "🛈 Freeze duration depends on the current depth",
        f" | [yellow]~ { round((152 * (2 ** depth)*5)/(60*60*24))} days[/yellow] at depth [yellow]{depth}[/yellow]",
        " 🔗 [link=https://docs.ethswarm.org/docs/learn/technology/incentives#penalties]Penalties[/link]",
    ]),
    "Reachable": "🔗 [link=https://docs.ethswarm.org/docs/bee/installation/connectivity]Connectivity[/link]",
    "Depth": "🔗 [link=https://docs.ethswarm.org/docs/learn/glossary#2-area-of-responsibility-related-depths]Depth[/link]",
    "Storage Radius": f"🛈 Should be [yellow]{network_depth}[/yellow]",
    "Staked Amount": "".join([
        "🔗 [link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking]Staking[/link]",
        " | [link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking#maximizing-staking-rewards]Maximizing Staking Rewards[/link]",
    ]),
    "xDAI": "".join([
        "🛈 Minimum [yellow]0.1 xDAI[/yellow] recommended",
        " 🔗 [link=https://docs.ethswarm.org/docs/bee/installation/fund-your-node]Fund Your Node[/link]",
        " | [link=https://docs.ethswarm.org/docs/learn/tokens#xdai]xDAI[/link]",
    ]),
    "xBZZ": "".join([
        "🛈 Minimum [yellow]1 xBZZ[/yellow] recommended ",
        "🔗 [link=https://docs.ethswarm.org/docs/bee/installation/fund-your-node]Fund Your Node[/link]",
        " | [link=https://docs.ethswarm.org/docs/learn/tokens#xbzz]xBZZ[/link]",
    ]),
    "Neighborhood Size": " | ".join([
        # "Typically more than [yellow]4[/yellow] nodes",
        "🔗 [link=https://docs.ethswarm.org/docs/learn/technology/disc#neighborhoods]Neighborhoods[/link]",
        "[link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking#neighborhood-selection]Neighborhood Selection[/link]",
        "[link=https://docs.ethswarm.org/docs/bee/installation/install#set-target-neighborhood-optional]Set Target Neighborhood[/link]",
        "[link=https://swarmscan.io/neighborhoods]Swarmscan[/link]",
    ]),
    "Reserve Size": "",
    "[cyan]LOTTERY[/cyan]": "",
    "Current Round": "🔗 [link=https://docs.ethswarm.org/docs/learn/technology/incentives#storage-incentives-details]Storage Incentives[/link]",
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
    "Neighborhood": f"{bin(nbhood)[2:].rjust(depth,'0')} (#{nbhood}/{neighborhood_count})",
    "Version": f"✅ {version}" if version == latest_bee else f"🟡 {version}",
    "Bee Mode": f"✅ {beeMode}" if beeMode == "full" else "🟡 {beeMode}",
    "Connected Peers": f"✅ {connectedPeers}" if connectedPeers > 149 else f"🟡 {connectedPeers}",
    "Pullsync Rate": f"✅ 0 (Synced)" if pullsyncRate == 0 else f"🟡 {pullsyncRate} (Syncing)",
    "Status": f"{get_bool(status == 'ok')} {status}",
    "Has Sufficient Funds": get_bool(hasSufficientFunds, True),
    "Is Fully Synced": get_bool(isFullySynced, True),
    "Not Frozen": get_bool(isFrozen == False, True),
    "Reachable": get_bool(reachability, True),
    "Depth": f"✅ {depth}" if depth == 10 else f"🟡 {depth}",
    "Storage Radius": f"✅ {storageRadius}" if storageRadius == 10 else f"🟡 {storageRadius}",
    "Staked Amount": f"✅ {stakedAmount} BZZ" if stakedAmount >= 10 else f"🟡 {stakedAmount} BZZ",
    "xDAI": f"✅ {nativeTokenBalance} xDAI" if nativeTokenBalance >= 0.1 else f"🟡 {nativeTokenBalance} xDAI",
    "xBZZ": f"✅ {bzzBalance} xBZZ" if bzzBalance >= 1 else f"🟡 {bzzBalance} xBZZ",
    "Neighborhood Size": neighborhoodSize,
    "Reserve Size": f"{(reserveSize * 4 * 512) / 1000 / 1000 / 1000:.3f} TB / {reserveSize} chunks",
    "[cyan]LOTTERY[/cyan]": "",
    "Current Round": current_round,
    "Playing Current Round": "🟡 Yes" if lastPlayedRound == current_round else "No",
    "Last Won Round": f"{'Not Yet' if lastWonRound == 0 else current_round - lastWonRound}{'' if lastWonRound == 0 else ' rounds ago'} ({lastWonRound})",
    "Last Frozen Round": f"{'Not Yet' if lastFrozenRound == 0 else current_round - lastFrozenRound}{'' if lastFrozenRound == 0 else ' rounds ago'} ({lastFrozenRound})",
    "Last Selected Round": f"{'Not Yet' if lastSelectedRound == 0 else current_round - lastSelectedRound}{'' if lastSelectedRound == 0 else ' rounds ago'} ({lastSelectedRound})",
    "Last Sample Duration": f"{lastSampleDuration / 60000000000:.1f} minutes"  if lastSampleDuration > 0  else "Not Yet (0)",
    "Rewards Collected": f"{format(float(reward) / 1e16, '.2f')} BZZ",
}

table = Table(show_header=True, header_style="bold magenta")

table.add_column("Section")
table.add_column("Key")
table.add_column("Value")
table.add_column("Hint / Links")

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
    f"🔗 [link=https://swarmscan.io/nodes/{overlay}]Swarmscan Link[/link] - Node",
)
table.add_section()
table.add_row(
    "[cyan]PERFORMANCE[/cyan]", "", "",
    "\n".join([
        "🔗 [link=https://docs.ethswarm.org/docs/bee/working-with-bee/staking#check-node-performance]Check Node Performance[/link]",
        "To check hardware performance, run:",
        f"[yellow]curl -X GET http://localhost:<BEE-API-PORT>/rchash/{network_depth}/aaaaaa | jq[/yellow]",
        "In the JSON response, the [yellow]Time[/yellow] duration should be less than [yellow]6[/yellow] minutes.",
    ]),
)   
console.print(table)