def calculate_last_leg_fee(sales, warehouse, product, shipping_rule):
    warehouse_map = warehouse.set_index('name')['type'].to_dict()
    fee_type_map = warehouse.set_index('name')['海外仓收费方式'].to_dict()
    product['内箱-毛重(磅)'] = pd.to_numeric(product['内箱-毛重(磅)'], errors='coerce').fillna(0)
    weight_map = product.set_index('名称')['内箱-毛重(磅)'].to_dict()
    size_map = product.set_index('名称')['尺寸判断'].fillna('大号标准尺寸').to_dict()
    shipping_rule['weight_min'] = pd.to_numeric(shipping_rule['weight_min'], errors='coerce')
    shipping_rule['weight_max'] = shipping_rule['weight_max'].replace('无限大', 1e9).astype(float)
    shipping_rule['base_fee'] = pd.to_numeric(shipping_rule['base_fee'], errors='coerce')
    shipping_rule['额外费用'] = shipping_rule['额外费用'].fillna("0")
    fees = []

    for idx, row in sales.iterrows():
        w_name = row['地点']
        w_type = warehouse_map.get(w_name, "")
        fee_type = fee_type_map.get(w_name, "")
        if w_type in ['分销仓', '国内仓', '港口仓', 'DI仓']:
            fees.append(0)
            continue

        sku = row['系统SKU']
        sz = size_map.get(sku, '大号标准尺寸')
        weight = weight_map.get(sku, 0)

        rule = shipping_rule[
            (shipping_rule['海外仓收费方式'].str.strip() == str(fee_type).strip()) &
            (shipping_rule['尺寸分段'] == sz) &
            (shipping_rule['weight_min'] <= weight) &
            (weight < shipping_rule['weight_max'])
        ]

        if rule.empty:
            fees.append(0)
            continue

        base_fee = rule['base_fee'].iloc[0]
        extra_formula = str(rule['额外费用'].iloc[0]).replace('（','(').replace('）',')').replace('x', str(weight))
        try:
            extra_fee = eval(extra_formula) if extra_formula.strip() != "0" else 0
        except:
            extra_fee = 0
        fees.append(base_fee + extra_fee)

    sales['尾程配送费'] = fees
    return sales
