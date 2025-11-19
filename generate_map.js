const unicode = require("unicode-properties");
const fs = require('fs'); // Budeme zapisovat do souboru
const MAX_UNICODE = 1114111 + 1;

class UnicodeTable {
    constructor() {
        this.map = []; // Použijeme pole
        let index = "!".codePointAt(0); // 33

        while (index < MAX_UNICODE) {
            // Přesně ta smyčka ze serveru
            while (!unicode.isAlphabetic(index)
                   && !unicode.isDigit(index)
                   && !unicode.isPunctuation(index)
                   && index < MAX_UNICODE) {
                index++;
            }

            if (index < MAX_UNICODE) {
                const c = String.fromCodePoint(index++);
                this.map.push(c);
            }
        }
    }
}

console.log("⏳ Generuji mapu (může to trvat minutu)...");
const table = new UnicodeTable();

// Spojíme všechny znaky do jednoho řetězce a uložíme
fs.writeFileSync("unicode_map.txt", table.map.join(""), "utf-8");
console.log(`✅ Mapa vygenerována a uložena do unicode_map.txt. Velikost: ${table.map.length} znaků.`);