def calculate_first_leg_fee(sales, warehouse, product):
    warehouse_map = warehouse.set_index('name')['type'].to_dict()
    first_leg_map = warehouse.set_index('name')['头程处理方式'].to_dict()
    product['内箱-体积(CM^3)'] = pd.to_numeric(product['内箱-体积(CM^3)'], errors='coerce').fillna(0)
    vol_map = product.set_index('名称')['内箱-体积(CM^3)'].to_dict()

    fees = []
    for idx, row in sales.iterrows():
        w_name = row['地点']
        first_leg_mode = first_leg_map.get(w_name, "正常计算头程")
        if first_leg_mode == "头程成本为0":
            fees.append(0)
        else:
            vol = vol_map.get(row['系统SKU'], 0)
            fees.append((8500 / 65000000) * vol)
    sales['头程费用'] = fees
    return sales
