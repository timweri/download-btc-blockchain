# download-btc-blockchain

Ever need to download parsed transaction data without wanting to run Bitcoin Core? 
This Python script will help you overcome Blockchain.info API Rate Limit using rotating procies and download the Blockchain data you need.

This script is written to use rotating proxies to constantly send requests to Blockchain.info API specifically.
However, some work is needed to make this run on other API.

This script allows you to potentially download years of Bitcoin blockchain data in 4 hours.

## How to run

### Dependencies

Make sure your Python is at least 3.6.
Install the dependencies:

```sh
pip install -r requirements.txt
```

### Run the script

The script takes in a few command line arguments:
- `--first-hash [required]`: The hash of the block to start from. The script downloads this block, and then continuously downloades the block before.
- `--output [required]`: Path to the folder to save the downloaded data.
- `--month`: If specified, the script will only download blocks from this month.

For example, run the script like so
```
python3 download.py --first-hash 01234 --output data
```

To find the desired hash, look up Blockchain.info API.
There is a API request where you can pass in the time and the API returns all the block hashes of that day.

The output will be written in files names `YYYY-MM-DD.out`.
The downloaded data will be grouped by date.
Expect each file to be about 30MB-80MB.

### How to run this faster

Each API request requires very little bandwidth.
The bottleneck is mostly the API reponse time and how fast your proxies are.
I used a premium rotating proxy service and it took, on average, 4s per request (per block).
In bad cases, the cost can spike up to 20-30s per block.
This makes it a very slow way to download, say, 2 years of blockchain data.

To speed this up, I recommend running multiple instances of the script in parallel.
From my experience, running multiple instances in parallel scale up the download speed linearly.
I was able to run 18 instances in parallel and the average cost per block was still 4s.
So I was able to speed up my download by 18 times, and there was definitely room for more instances.
Of course, YMMV depending on your internet and hardware.

To run multiple instances in parallel without them colliding, I limit each instance to download 1 month.
This is what the `--month` option is for.
Once the current hash doesn't belong to that target month, the download script terminates.
It takes around 4 hours to download a month of data.

#### Example usage

You want to download blocks in year 2021.
First, look up last block hash of each month in 2021

Then, run the script like so:
```
python3 download.py --first-hash <last_hash_of_december> --output data --month 12
python3 download.py --first-hash <last_hash_of_november> --output data --month 11
python3 download.py --first-hash <last_hash_of_october> --output data --month 10
...
```
