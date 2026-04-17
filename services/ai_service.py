import os
import json
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def encode_image(image_data):
    return base64.b64encode(image_data).decode('utf-8')

def analyze_receipt_image(image_data, ocr_text=None):
    """
    Vision + OCR Assisted Document Understanding
    OCR text is the PRIMARY source, image is fallback.
    """
    base64_image = encode_image(image_data)

    prompt = f"""
    You are an expert Environmental Data Scientist analyzing a purchase receipt.

    IMPORTANT INSTRUCTION:
    - Use the OCR TEXT as the PRIMARY source of truth.
    - Only use the IMAGE if OCR text is incomplete or unclear.
    - DO NOT guess values that are not present.

    ================ OCR TEXT =================
    {ocr_text}
    =========================================

    >>> CRITICAL CURRENCY & ECONOMIC CONTEXT RULE:
    1. Detect the original currency (IDR, USD, EUR, SGD, etc).
    2. CONVERT ALL prices to IDR (Indonesian Rupiah).
    Conversion rates:
    - USD → 15,500 IDR
    - EUR → 16,500 IDR
    - SGD → 11,500 IDR

    3. COST OF LIVING NORMALIZATION (VERY IMPORTANT):
    - If origin currency is IDR:
    Use Indonesian market standard (example: meal max ≈ 50,000 IDR).
    - If origin currency is USD / EUR / SGD:
    Scale the max_price_per_unit to match that country's cost of living,
    then convert the final value to IDR.

    BAD EXAMPLE (WRONG):
    Item: Salad $10 → 155,000 IDR
    max_price_per_unit: 50,000 IDR 

    GOOD EXAMPLE (CORRECT):
    Item: Salad $10 → 155,000 IDR
    max_price_per_unit: $15 → 232,500 IDR 

    TASKS:
    1. Extract item name, quantity, and TOTAL price (IDR).
    2. Autonomously determine item category.
    3. If fuel is detected, calculate volume:
    volume = total_price_IDR / 13,500
    4. Fill market_context accurately:
    - max_price_per_unit (IDR)
    - max_weight_per_unit (kg)
    - emission_factor
    - packaging_factor

    OUTPUT FORMAT (STRICT JSON):
    {{
    "items": [
        {{
        "name": "Item Name",
        "total_price": 155000,
        "quantity": 1,
        "category": "FOOD",
        "market_context": {{
            "max_price_per_unit": 232500,
            "max_weight_per_unit": 0.5,
            "emission_factor": 1.5,
            "packaging_factor": 0.1
        }}
        }}
    ]
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )

        response_text = completion.choices[0].message.content
        parsed_data = json.loads(response_text)

        return parsed_data.get("items", [])

    except json.JSONDecodeError:
        print("JSON Error: AI output invalid")
        print(response_text)
        return []
    except Exception as e:
        print(f"Groq Vision Error: {e}")
        return []


def generate_comparison(total_co2):
    
    prompt = f"""
    Data Emisi: {total_co2:.2f} kg CO2.
    
    Tugas: Carikan SATU analogi yang UNIK dan KREATIF untuk menggambarkan beban emisi ini. 
    
    ATURAN MUTLAK:
    1. Kalimat HARUS diawali persis dengan: "Total emisi yang kamu hasilkan"
    2. LARANGAN KERAS: JANGAN gunakan analogi "Lampu LED" atau "Lampu Bohlam" lagi (cari variasi lain: misal streaming film, produksi plastik, es kutub, napas manusia, jarak motor, daging sapi, dll).
    3. Pilih satu saja yang paling pas, jangan digabung-gabung.
    4. Buat user merasa "Wah, segitu ya ternyata?".
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9, 
            max_tokens=150,
        )
        return completion.choices[0].message.content.strip()
    except:
        return f"Total emisi yang kamu hasilkan setara dengan mengemudi mobil sejauh {total_co2 / 0.2:.1f} KM."