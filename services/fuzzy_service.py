import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

def calculate_unit_weight(unit_price, context):
    """
    Menghitung berat estimasi untuk SATU unit barang.
    UPDATED: Support Dynamic Scaling (Auto-adjust untuk Rupiah/Dollar)
    """
    #Ambil nilai referensi dari Context AI, default ke IDR (50k)
    max_p = float(context.get('max_price_per_unit', 50000.0)) 
    max_w = float(context.get('max_weight_per_unit', 1.0))
    
    #Dynamic Scaling
    if unit_price > max_p:
        max_p = unit_price * 1.2
    
    if max_p <= 0: max_p = 50000.0
    if max_w <= 0: max_w = 1.0

    #rentang data
    step_p = max_p / 50.0
    step_w = max_w / 50.0
    
    if step_p == 0: step_p = 1
    if step_w == 0: step_w = 0.1

    x_price = np.arange(0, max_p + step_p, step_p)
    x_weight = np.arange(0, max_w + step_w, step_w)

    price = ctrl.Antecedent(x_price, 'price')
    weight = ctrl.Consequent(x_weight, 'weight')

    price['low']    = fuzz.trimf(x_price, [0, 0, max_p * 0.4])
    price['medium'] = fuzz.trimf(x_price, [0, max_p * 0.5, max_p])
    price['high']   = fuzz.trimf(x_price, [max_p * 0.6, max_p, max_p])

    weight['light'] = fuzz.trimf(x_weight, [0, 0, max_w * 0.4])
    weight['medium']= fuzz.trimf(x_weight, [0, max_w * 0.5, max_w])
    weight['heavy'] = fuzz.trimf(x_weight, [max_w * 0.6, max_w, max_w])

    rule1 = ctrl.Rule(price['low'], weight['light'])
    rule2 = ctrl.Rule(price['medium'], weight['medium'])
    rule3 = ctrl.Rule(price['high'], weight['heavy'])

    weight_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
    sim = ctrl.ControlSystemSimulation(weight_ctrl)
    
    sim.input['price'] = min(unit_price, max_p)
    
    try:
        sim.compute()
        return sim.output['weight']
    except Exception as e:
        print(f"Fuzzy Error: {e}. Fallback to medium weight.")
        return max_w * 0.5