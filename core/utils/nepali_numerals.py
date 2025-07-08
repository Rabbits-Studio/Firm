# Create this file to handle numeral conversions

nepali_to_english = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9', '.': '.'
}

english_to_nepali = {v: k for k, v in nepali_to_english.items()}

def nep_to_eng(num_str):
    return ''.join(nepali_to_english.get(ch, ch) for ch in num_str)

def eng_to_nep(num_str):
    return ''.join(english_to_nepali.get(ch, ch) for ch in str(num_str))
