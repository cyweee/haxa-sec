#!/bin/bash

# check if file name is given
if [ -z "$1" ]; then
    echo "Error: give me a file name."
    echo "Example: ./decode_loop.sh a.txt"
    exit 1
fi

content=$(cat "$1")
count=0

echo "Starting decode loop (step 0)..."

while true; do
    # try to decode (hide 'invalid input' errors)
    decoded_content=$(echo -n "$content" | base64 -d 2>/dev/null)

    if [ $? -ne 0 ]; then
        # stop when decoding fails
        echo "-----------------------------------"
        echo "STOP. Decoded $count times."
        echo "Final result (no more Base64):"
        echo "-----------------------------------"
        echo "$content"
        break
    else
        # success → continue
        content="$decoded_content"
        count=$((count + 1))
        echo "Step $count... OK"
    fi
done
