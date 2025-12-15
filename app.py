from flask import Flask, request, jsonify
from flask_cors import CORS
from services.ai_service import analyze_receipt_image, generate_comparison
from services.fuzzy_service import calculate_unit_weight

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    image_data = file.read()

    #computer vision service
    items_data = analyze_receipt_image(image_data)
    
    if not items_data:
        return jsonify({"error": "Failed to analyze image"}), 500

    results = []
    grand_total_co2 = 0
    
    #gabungan data AI + hitungan fuzzy
    for item in items_data:
        qty = int(item.get('quantity', 1))
        total_price = float(item.get('total_price', 0))
        unit_price = total_price / qty if qty > 0 else total_price
        
        #panggil fuzzy
        context = item.get('market_context', {})
        unit_weight_est = calculate_unit_weight(unit_price, context)
        
        #hitung fisika sederhana
        total_weight = unit_weight_est * qty
        mat_factor = float(context.get('emission_factor', 1.0))
        pack_factor = float(context.get('packaging_factor', 0.0))
        
        total_item_co2 = (total_weight * mat_factor) + (qty * pack_factor)
        grand_total_co2 += total_item_co2
        
        results.append({
            "name": item['name'],
            "qty": qty,
            "category": item.get('category', 'GENERAL'),
            "total_price": total_price,
            "unit_weight_est": round(unit_weight_est, 3),
            "co2_kg": round(total_item_co2, 2)
        })

    #text service untuk bandingin
    comparison_text = generate_comparison(grand_total_co2)
    
    min_co2 = grand_total_co2 * 0.8
    max_co2 = grand_total_co2 * 1.2

    return jsonify({
        "status": "success",
        "data": {
            "items": results,
            "total_co2_kg": round(grand_total_co2, 1),
            "range": {
                "min": round(min_co2, 1),
                "max": round(max_co2, 1)
            },
            "comparison": comparison_text
        }
    })

if __name__ == '__main__':
    app.run()