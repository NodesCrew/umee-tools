# Umeevengers-1c

TX Spam challenge


1. Withdraw all rewards from your 1c validator to self-delegate address
```bash
umeed tx distribution withdraw-rewards VALOPER_HERE --chain-id $UMEE_CHAIN --gas=auto --fees=200uumee --commission --yes --from WALLET_HERE
umeed tx distribution withdraw-all-rewards --from WALLET_HERE --chain-id $UMEE_CHAIN --fees=200uumee --yes
```

2. Receive your 1000Umee to self-delegate address [via form](https://docs.google.com/forms/u/0/d/1A7rd-NGIGol7kS8tuYDf87JnToEXUN2ckTP752l4xCc/viewform?edit_requested=true)
3. Create N wallets with create_keys.py
```bash
pip3 install click
python3 challenge.py create-keys --keys-number 5
```
4. Put your self-delegate wallet into "keys/main.json"
```json
umeed keys show WALLET_HERE --output json
```
5. Load your created wallets from self-delegate address balance
```bash
python3 challenge.py load-funds --fee=100 --limit=10000
```
