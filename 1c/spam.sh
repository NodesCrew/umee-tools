#!/bin/bash

PATH_TO_SERVICE='{BINARY}'
KEY_PASSWORD='{KEYRING_PASSWORD}'
ACCOUNT='{SEND_FROM}'
TO_ADDRESS='{SEND_TO}'
CHAIN_ID='{CHAIN_ID}'
MEMO='{VALOPER}'
DENOM=uumee
SEND_AMOUNT=1
FEE_AMOUNT=1
NODE='{RPC_URL}'

SEQ=$(${PATH_TO_SERVICE} q account ${ACCOUNT} -o json | jq '.sequence | tonumber')



while :
do
    CURRENT_BLOCK=$(curl -s ${NODE}/abci_info | jq -r .result.response.last_block_height)

    TX_RESULT_RAW_LOG=$(echo $KEY_PASSWORD | $PATH_TO_SERVICE tx bank send $ACCOUNT $TO_ADDRESS \
        ${SEND_AMOUNT}${DENOM} \
        --fees ${FEE_AMOUNT}${DENOM} \
        --chain-id $CHAIN_ID \
        --output json \
        -s $SEQ \
        --timeout-height $(($CURRENT_BLOCK + 5)) -y | \
        jq '.raw_log')
    SEQ=$(($SEQ + 1))

    if [[ "$TX_RESULT_RAW_LOG" == *"incorrect account sequence"* ]]; then
        sleep 10
        SEQ=$(${PATH_TO_SERVICE} q account ${ACCOUNT} -o json | jq '.sequence | tonumber')
        echo $SEQ
    elif [[ "$TX_RESULT_RAW_LOG" == *"insufficient fees; got"* ]]; then
        echo $TX_RESULT_RAW_LOG


        FEE_AMOUNT=$(echo "$FEE_AMOUNT + 25" | bc -l)
        echo "Out of gas. Increment fee to $FEE_AMOUNT"

    else
        FEE_AMOUNT=$(echo "$FEE_AMOUNT - 1" | bc -l)
        echo "Success. Decrement fee to $FEE_AMOUNT"
    fi

    echo $SEQ
done