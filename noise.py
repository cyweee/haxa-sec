from PIL import Image
import numpy as np


def extract_bit_plane(image_path, bit_index):
    # bit_index: 0 pro LSB, 1 pro další, atd.

    img = Image.open(image_path)
    data = np.array(img)

    print(f"Analyzuji bitovou rovinu {bit_index} (Bit Plane {bit_index})")

    channels = ['Red', 'Green', 'Blue']

    # 2**bit_index je maska pro daný bit (např. 2 pro Bit 1, 4 pro Bit 2)
    mask = 2 ** bit_index

    for i, channel_name in enumerate(channels):
        channel_data = data[:, :, i]

        # 1. Izolace bitu: (channel_data & mask)
        # 2. Posun bitu: // mask (vrátí buď 0, nebo 1)
        # 3. Zesílení: * 255 (pro vytvoření černobílého obrazu)
        bit_plane = ((channel_data & mask) // mask) * 255

        # Vytvoření a uložení nového obrázku
        result_img = Image.fromarray(bit_plane.astype(np.uint8))
        output_filename = f"odhaleny_{channel_name}_Bit{bit_index}.png"
        result_img.save(output_filename)
        print(f"--> Uložen: {output_filename} (ZKONTROLUJ tento soubor!)")


# --- SPUSŤ TENTO NOVÝ KÓD ---

# Zkusíme extrahovat Bit 1 (druhý nejméně významný)
extract_bit_plane("noise.bmp", 1)

# Zkusíme extrahovat Bit 2, jen pro jistotu
# extract_bit_plane("noise.bmp", 2)