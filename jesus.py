import pandas as pd

# Načtení dat
people = pd.read_csv('people.csv')
gifts = pd.read_csv('gifts.csv')

# 1. Počet lidí
num_people = len(people)

# 2. Celkový počet dárků
num_gifts = len(gifts)

# 3. Nejčastější dárek
most_frequent_gift = gifts['gift'].value_counts().idxmax()

# 4. Město s nejvíce uhlím (COAL)
# Propojíme tabulky, abychom věděli, v jakém městě kdo bydlí
merged = gifts.merge(people, on='person_id')
coal_data = merged[merged['gift'] == 'COAL']
city_with_most_coal = coal_data['city'].value_counts().idxmax()

# 5. Unikátní dárek (vyskytuje se právě jednou)
gift_counts = gifts['gift'].value_counts()
unique_gift = gift_counts[gift_counts == 1].index[0]

# 6. Kdo dostane nejvíce dárků
top_person_id = gifts['person_id'].value_counts().idxmax()
top_person_name = people[people['person_id'] == top_person_id]['name'].values[0]

# Výpis výsledků
print(f"Vlajka 01 (Lidé): haxagon{{{num_people}}}")
print(f"Vlajka 02 (Dárky): haxagon{{{num_gifts}}}")
print(f"Vlajka 03 (Nejčastější): haxagon{{{most_frequent_gift}}}")
print(f"Vlajka 04 (Město uhlí): haxagon{{{city_with_most_coal}}}")
print(f"Vlajka 05 (Unikátní): haxagon{{{unique_gift}}}")
print(f"Vlajka 06 (Nejvíc dárků): haxagon{{{top_person_name}}}")