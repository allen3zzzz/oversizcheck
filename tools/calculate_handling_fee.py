def calculate_handling_fee(sales, warehouse, product, handling_rule):
    warehouse_map = warehouse.set_index('name')['type'].to_dict()
    product['内箱-毛重(KG)'] = pd.to_numeric(product['内箱-毛重(KG)'], errors='coerce').fillna(0)
    weight_map = product.set_index('名称')['内箱-毛重(KG)'].to_dict()

    handling_rule['weight_min'] = pd.to_numeric(handling_rule['weight_min'], errors='coerce').fillna(0)
    handling_rule['weight_max'] = handling_rule['weight_max'].replace('无限大', 1e9).astype(float)
    handling_rule['收费/件'] = pd.to_numeric(handling_rule['收费/件'], errors='coerce').fillna(0)
    handling_rule['额外费用'] = handling_rule['额外费用'].fillna("0")

    fees = []
    for idx, row in sales.iterrows():
        w_name = row['地点']
        w_type = warehouse_map.get(w_name, "")
        if w_type in ['分销仓', '国内仓', '港口仓', 'DI仓']:
            fees.append(0)
            continue

        sku = row['系统SKU']
        weight = weight_map.get(sku, 0)
        rule = handling_rule[
            (handling_rule['仓库'] == w_type) &
            (handling_rule['weight_min'] <= weight) &
            (weight < handling_rule['weight_max'])
        ]
        if rule.empty:
            rule = handling_rule[
                (handling_rule['仓库'] == '华云') &
                (handling_rule['weight_min'] <= weight) &
                (weight < handling_rule['weight_max'])
            ]
        if not rule.empty:
            base_fee = rule['收费/件'].iloc[0]
            extra_formula = str(rule['额外费用'].iloc[0]).replace('x', str(weight))
            try:
                extra_fee = eval(extra_formula) if extra_formula.strip() != "0" else 0
            except:
                extra_fee = 0
            fees.append(base_fee + extra_fee)
        else:
            fees.append(0)
    sales['操作费'] = fees
    return sales
