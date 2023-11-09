import sys
import requests
from rich.console import Console
from rich.table import Table
from rich import print


if len(sys.argv) < 2:
    print("Error: debug port is required.")
    print("USAGE: [cyan]python3 bee_checkup.py <BEE_DEBUG_PORT>[/cyan]")
    sys.exit(1)

port = sys.argv[1]

def getBool(b):
    return "✅" if b else "❌"

# Fetch redistribution state
redistributionstate_url = f"http://localhost:{port}/redistributionstate"
redistributionstate_response = requests.get(redistributionstate_url)
redistributionstate_data = redistributionstate_response.json()
hasSufficientFunds = redistributionstate_data['hasSufficientFunds']
isFullySynced = redistributionstate_data['isFullySynced']
isFrozen = redistributionstate_data['isFrozen']
lastPlayedRound = redistributionstate_data['lastPlayedRound']
round = redistributionstate_data['round']
phase = redistributionstate_data['phase']
lastWonRound = redistributionstate_data['lastWonRound']
lastFrozenRound = redistributionstate_data['lastFrozenRound']
lastSelectedRound = redistributionstate_data['lastSelectedRound']
lastSampleDuration = redistributionstate_data['lastSampleDuration']
block = redistributionstate_data['block']
reward = redistributionstate_data['reward']

# Fetch topology
topology_url = f"http://localhost:{port}/topology"
topology_response = requests.get(topology_url)
topology_data = topology_response.json()
depth = topology_data['depth']
reachability = topology_data['reachability']

# Fetch stake
stake_url = f"http://localhost:{port}/stake"
stake_response = requests.get(stake_url)
stake_data = stake_response.json()
stakedAmount = stake_data['stakedAmount']

# Fetch reservestate
reservestate_url = f"http://localhost:{port}/reservestate"
reservestate_response = requests.get(reservestate_url)
reservestate_data = reservestate_response.json()
radius = reservestate_data['radius']
storageRadius = reservestate_data['storageRadius']

# Fetch rstatus
rstatus_url = f"http://localhost:{port}/status"
rstatus_response = requests.get(rstatus_url)
rstatus_data = rstatus_response.json()
reserveSize = rstatus_data['reserveSize']
neighborhoodSize = rstatus_data['neighborhoodSize']

# Fetch wallet
wallet_url = f"http://localhost:{port}/wallet"
wallet_response = requests.get(wallet_url)
wallet_data = wallet_response.json()
bzzBalance = wallet_data['bzzBalance']
nativeTokenBalance = wallet_data['nativeTokenBalance']
walletAddress = wallet_data['walletAddress']

# Fetch health
health_url = f"http://localhost:{port}/health"
health_response = requests.get(health_url)
health_data = health_response.json()
version = health_data['version']
status = health_data['status']

# Fetch addresses
addresses_url = f"http://localhost:{port}/addresses"
addresses_response = requests.get(addresses_url)
addresses_data = addresses_response.json()
overlay = addresses_data['overlay']

# Populate the output dictionary
out = {
    'port': port,
    'walletAddress': f"[link=https://gnosisscan.io/address/{walletAddress}]{walletAddress[0:6]}...{walletAddress[-4:]}[/link]",
    'overlay': f"[link=https://swarmscan.io/nodes/{overlay}]{overlay[0:6]}...{overlay[-4:]}[/link]",
    'version': version.split('-')[0],
    'reserveSize': f"{(reserveSize * 4 * 512) / 1000 / 1000 / 1000:.3f} TB",
    'status': getBool(status == 'ok'),
    'hasSufficientFunds': getBool(hasSufficientFunds),
    'isFullySynced': getBool(isFullySynced),
    'notFrozen': getBool(isFrozen == False),
    'reachability': getBool(reachability),
    'depth': depth,
    'radius': radius,
    'storageRadius': storageRadius,
    'neighborhoodSize': neighborhoodSize,
    'currentlyPlayingGame': '🟡' if lastPlayedRound == round else 'No',
    'stakedAmount': f"{stakedAmount[:-16]} BZZ",
    'BZZ': f"{float(bzzBalance) / 10 ** 16} xBZZ",
    'DAI': f"{float(nativeTokenBalance) / 10 ** 18} xDAI",
    'currentRound': round,
    'lastWonRound': f"{lastWonRound} ({0 if lastWonRound == 0 else round - lastWonRound} {'- never' if lastWonRound == 0 else 'rounds ago'})",
    'lastFrozenRound': f"{lastFrozenRound} ({0 if lastFrozenRound == 0 else round - lastFrozenRound} {'- never' if lastFrozenRound == 0 else 'rounds ago'})",
    'lastSelectedRound': f"{lastSelectedRound} ({0 if lastSelectedRound == 0 else round - lastSelectedRound} {'- never' if lastSelectedRound == 0 else 'rounds ago'})",
    'lastSampleDuration': f"{lastSampleDuration / 60000000000:.1f} m",
    'block': block,
    'rewardsCollected': f"{format(float(reward) / 1e16, '.2f')} BZZ"
}



# Create a new table
table = Table(show_header=True, header_style="bold magenta")

# Add columns to the table
table.add_column("Key")
table.add_column("Value")

# Add rows from the dictionary
for key, value in out.items():
    table.add_row(key, str(value) )

# Create a console object and print the table
console = Console()
console.print(table)