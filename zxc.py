n = 35518926326580479913012365689128912908157
print(n.to_bytes((n.bit_length() + 7) // 8, 'big').decode('latin-1'))