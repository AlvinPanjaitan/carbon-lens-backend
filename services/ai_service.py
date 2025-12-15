import os
import json
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def encode_image(image_data):
    return base64.b64encode(image_data).decode('utf-8')

def analyze_receipt_image(image_data):
    """
    Tahap 1: Vision - PROMPT UPDATE (AUTO CURRENCY CONVERSION)
    """
    base64_image = encode_image(image_data)
    
    prompt = """
    You are an expert Environmental Data Scientist. Analyze this receipt.
    
    >>> CRITICAL CURRENCY & ECONOMIC CONTEXT RULE (Wajib Baca):
    1. Detect the currency (IDR, USD, EUR, etc).
    2. CONVERT EVERYTHING TO IDR (Indonesian Rupiah) for the 'total_price'.
       Rates: $1=15500, €1=16500, SG$1=11500.
    
    3. THE KEY TO PRECISION (Dealing with High Cost of Living):
       When determining 'max_price_per_unit' in 'market_context':
       - If Origin is Indonesia (IDR): Use Indonesian standard (e.g., Meal Max = 50,000 IDR).
       - If Origin is USA/Europe (USD/EUR): You MUST SCALE UP the standard to match that country's cost of living.
         
       EXAMPLE FAIL (Don't do this):
       Item: Salad $10 (155,000 IDR). Max_Price set to Indo standard (50,000 IDR).
       Result: 155k > 50k -> System thinks it's HUGE/HEAVY. (WRONG).
       
       EXAMPLE CORRECT (Do this):
       Item: Salad $10 (155,000 IDR). Max_Price set to NY standard ($15 -> 232,500 IDR).
       Result: 155k is smaller than 232k -> System thinks it's Normal Portion. (CORRECT).
    
    TASK:
    1. Extract Item Name, Total Price (IDR), and Quantity.
    2. Determine CATEGORY autonomously.
    3. CALCULATE FUEL VOLUME (If applicable):
       - Volume = Total_Price_IDR / 13500.
    
    4. FILL MARKET CONTEXT (Crucial for Weight Estimation):
       - max_price_per_unit: The price of a "Large/Premium" version of this item IN THE ORIGIN COUNTRY context, converted to IDR.
       - max_weight_per_unit: The weight (kg) of that "Large" version.
       
    OUTPUT FORMAT (JSON):
    {
      "items": [
        {
          "name": "Item Name",
          "total_price": 155000, 
          "quantity": 1,
          "category": "FOOD",
          "market_context": {
              "max_price_per_unit": 232500, 
              "max_weight_per_unit": 0.5,
              "emission_factor": 1.5,
              "packaging_factor": 0.1
          }
        }
      ]
    }
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
        print(f"Error JSON: AI Output rusak.\nRaw: {response_text}")
        return []
    except Exception as e:
        print(f"Error Groq Vision: {e}")
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