# Umeevengers-1c

TX Spam challenge

1. Clone repository
```bash
git clone https://github.com/myuriy/umee-tools.git
cd umee-tools/1c
pip3 install click
apt install screen -y
```
2. Withdraw all rewards from your 1c validator to self-delegate address
```bash
umeed tx distribution withdraw-rewards VALOPER_HERE --chain-id $UMEE_CHAIN --gas=auto --fees=200uumee --commission --yes --from WALLET_HERE
umeed tx distribution withdraw-all-rewards --from WALLET_HERE --chain-id $UMEE_CHAIN --fees=200uumee --yes
```

3. Receive your 1000Umee to self-delegate address [via form](https://docs.google.com/forms/u/0/d/1A7rd-NGIGol7kS8tuYDf87JnToEXUN2ckTP752l4xCc/viewform?edit_requested=true)
4. Create config_local.py 
```python
# coding: utf-8

KEYRING_PASSWORD = b"password\n"
BINARY = "/root/go/bin/umeed"
VALOPER = "umeevaloper13zz9xkvgakzl7eq4sh4a0qnhpm7q8lyuul2k68"
```
5. Create N wallets with create_keys.py
```bash
python3 challenge.py create-keys --keys-number 5
```
6. Put your self-delegate wallet into "keys/main.json"
```bash
umeed keys show WALLET_HERE --output json
```
7. Load your created wallets from self-delegate address balance (--limit is the amount that can be distributed among the keys in uumee).
```bash
python3 challenge.py load-funds --fee=100 --limit=10000
```
8. Import all keys on 2,3..N server
```bash
# Repeat step 1, step 4 on new server
# Copy umee-tools/1c/keys/ to new server:umee-tools/1c/keys/
python3 challenge.py import-keys
```
9. Generate workers on 2,3..N server
```bash
python3 challenge.py generate-workers
```
10. Start TX spam
```bash
bash screen.sh
```
11. Stop TX spam (warning! all screen sessions will be killed, not only started from screen.sh)
```bash
pkill screen
```
