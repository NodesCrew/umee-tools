#!/bin/bash

PATH_TO_SERVICE='{BINARY}'
KEY_PASSWORD='{KEYRING_PASSWORD}'
ACCOUNT=${1}
TO_ADDRESS=${2}
CHAIN_ID=umeevengers-1c
MEMO='{VALOPER}'
DENOM=uumee
SEND_AMOUNT=1
FEE_AMOUNT=200
NODE=${3:-"http://localhost:26657"}

SEQ=$(${PATH_TO_SERVICE} q account ${ACCOUNT} -o json | jq '.sequence | tonumber')



while :
do
    CURRENT_BLOCK=$(curl -s ${NODE}/abci_info | jq -r .result.response.last_block_height)

    TX_RESULT_RAW_LOG=$(echo $KEY_PASSWORD | $PATH_TO_SERVICE tx bank send $ACCOUNT $TO_ADDRESS \
        ${SEND_AMOUNT}${DENOM} \
        --fees ${FEE_AMOUNT}${DENOM} \
        --chain-id $CHAIN_ID \
        --note $MEMO \
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
	echo $TX_RESULT_RAW_LOG
    fi

    echo $SEQ
done