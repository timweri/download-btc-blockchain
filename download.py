import requests
import sys
import argparse
from datetime import datetime, date
import time
import os
import shutil
import json
import argparse
from lxml.html import fromstring
from itertools import cycle

arg_parser = argparse.ArgumentParser(description="Configure blockchain download")
arg_parser.add_argument("--first-hash", nargs=1, help="Start from this block", type=str, required=True)
arg_parser.add_argument("--output", nargs=1, help="Output folder path", type=str, required=True)
arg_parser.add_argument("--month", nargs=1, help="Choose a month to download", type=int)
arg_parser.add_argument("--retries", nargs=1, help="Number of retries before quitting", type=int)
arg_parser.add_argument("--timeout", nargs=1, help="Requests timeout", type=int)
args = arg_parser.parse_args()

# Configure max retries
req = requests.Session()
# adapter = requests.adapters.HTTPAdapter(max_retries=2)
# req.mount('http://', adapter)
# req.mount('http://', adapter)

# Custom User-Agent
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'
}

# TODO: Add your rotating proxies here
proxy_pool = cycle([
    {
        "http": "{rotating_proxies}",
        "https": "{rotating_proxies}",
    }
])
proxy = next(proxy_pool)

current_hash = args.first_hash[0]
output_path = args.output[0]
n_retires = 10
timeout = 20
target_month = None

if args.month:
    target_month = args.month[0]

if args.retires:
    n_retires = args.retires[0]

if args.timeout:
    timeout = args.timeout[0]

print(f"Starting block: {current_hash}\n")

# Create output folder if not exists
if not os.path.exists(output_path):
    os.mkdir(output_path)

total_time = 0
total_block_count = 0
start_time = time.time()

try:
    current_date = None
    outfile = None

    while True:
        print(f"Downloading block {current_hash}")

        i = 0
        while True:
            try:
                tmp = time.time()
                proxy = next(proxy_pool)
                res = req.get(f"https://blockchain.info/rawblock/{current_hash}", proxies=proxy, timeout=timeout, headers=headers)
                res = res.json()
                print(f"Downloaded block in: {time.time() - tmp} s")
            except requests.exceptions.RequestException as ex:
                i += 1
                if i >= n_retires:
                    raise ex
                continue
            break

        current_time = res["time"]

        current_datetime = datetime.fromtimestamp(current_time)
        print(f"Current block timestamp: {current_datetime}")

        if target_month and current_datetime.month != target_month:
            print(f"Target month mismatch: {target_month} != {current_datetime.month}")
            break

        new_date = date(current_datetime.year, current_datetime.month, current_datetime.day)
        if current_date != new_date:
            if outfile:
                outfile.close()

            current_date = new_date

            outfilename = f"{output_path}/{current_date}.out"
            outfile = open(outfilename, "a")
            print(f"Beginning writing data for day {current_date}")

        # Drop first coinbase TX
        for tx in res["tx"][1:]:
            data = [tx["hash"][:8], str(tx["tx_index"])]
            amount = 0

            vin_sz = tx["vin_sz"] 
            vout_sz = tx["vout_sz"] 
            data.append(str(vin_sz))

            vin_count = 0

            for txin in tx["inputs"]:
                if "prev_out" not in txin:
                    data.append("NA")
                elif "addr" not in txin["prev_out"]:
                    data.append("NA")
                else:
                    data.append(txin["prev_out"]["addr"])

                vin_count += 1

            if vin_count != vin_sz:
                print(f"WARNING: tx {tx['hash']} indexed {tx['tx_index']} : vin_sz mismatch : {vin_count} != {vin_sz}")

            data.append(str(vout_sz))
            vout_count = 0

            for txout in tx["out"]:
                if "addr" not in txout:
                    data.append("NA")
                else:
                    data.append(txout["addr"])

                if "value" in txout:
                    amount += txout["value"]

                vout_count += 1

            if vout_count != vout_sz:
                print(f"WARNING: tx {tx['hash']} indexed {tx['tx_index']} : vout_sz mismatch : {vout_count} != {vout_sz}")

            data.append(str(amount))

            outfile.write(",".join(data) + "\n")
        
        print(f"Saved data of block {current_hash}")

        current_hash = res["prev_block"]
        total_time = time.time() - start_time
        total_block_count += 1

        print(f"Average time per block: {total_time / total_block_count} s")

    if outfile:
        outfile.close()
except KeyboardInterrupt:
    if outfile:
        outfile.close()
