import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests
import json

# 1. NAČTENÍ A TRÉNOVÁNÍ
# Předpokládáme, že frogs_data.csv je ve stejném adresáři
data = pd.read_csv('frogs_data.csv')

# Vstupy (MFCCs) a cílová hodnota (Species)
# Poznámka: Dataset obvykle obsahuje sloupce MFCCs_ 1 až MFCCs_22
X = data.filter(regex='MFCCs_')
y = data['Species']

# Inicializace a trénink modelu
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

print("Model je natrénován a připraven!")

# 2. ZÍSKÁNÍ DAT Z API
URL_GET = "http://13.61.6.159/get_frogs"
URL_POST = "http://13.61.6.159/submit_frogs"

print("Stahuji testovací data...")
response = requests.get(URL_GET)
test_data = response.json() # Seznam 100 slovníků

# Převod JSONu na DataFrame pro model
# Důležité: Klíče v JSONu musí přesně odpovídat názvům sloupců při trénování
X_test = pd.DataFrame(test_data)

# 3. PŘEDPOVĚĎ
print("Provádím klasifikaci...")
predictions = model.predict(X_test)

# Převod ndarray na list (aby šel serializovat do JSON)
predictions_list = predictions.tolist()

# 4. ODESLÁNÍ VÝSLEDKŮ
print("Posílám výsledky zpět...")
submit_response = requests.post(
    URL_POST,
    json=predictions_list,
    headers={"Content-Type": "application/json"}
)

# Výpis odpovědi (doufejme, že s vlajkou!)
print("Status:", submit_response.status_code)
print("Odpověď serveru:", submit_response.text)