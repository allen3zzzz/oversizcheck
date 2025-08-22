import pandas as pd

def split_orders(df):
    df['不含税总价'] = pd.to_numeric(df['不含税总价'], errors='coerce').fillna(0)
    df['数量'] = pd.to_numeric(df['数量'], errors='coerce').fillna(1)
    df['拆单不含税总价'] = df['不含税总价'] / df['数量']
    df = df.loc[df.index.repeat(df['数量'])].reset_index(drop=True)
    df['数量'] = 1
    return df

def calculate_fifo_cost(sales, purchase):
    purchase_df = purchase.copy()
    purchase_df['数量'] = pd.to_numeric(purchase_df['数量'], errors='coerce').fillna(0)
    purchase_df['出现次数'] = purchase_df.groupby('文档编号').cumcount() + 1
    purchase_df['入库批次号'] = purchase_df['文档编号'].astype(str) + "-" + purchase_df['出现次数'].astype(str)
    purchase_df['剩余库存'] = purchase_df['数量']
    purchase_df['含税单价'] = pd.to_numeric(purchase_df.get('含税单价', 0), errors='coerce').fillna(0)

    sales_df = sales.copy()
    sales_df['数量'] = pd.to_numeric(sales_df['数量'], errors='coerce').fillna(0)
    sales_df = sales_df.sort_values(['系统SKU', '日期'])

    deduct_records = []

    for sku, group in sales_df.groupby('系统SKU'):
        stock = purchase_df[purchase_df['货品'] == sku].copy()
        stock = stock.sort_values(['日期', '入库批次号'])
        p_idx = 0

        for _, sale in group.iterrows():
            sale_qty = sale['数量']
            remaining_qty = sale_qty
            sale_data = sale.to_dict()

            while remaining_qty > 0 and p_idx < len(stock):
                batch = stock.iloc[p_idx]
                avail_qty = batch['剩余库存']
                if avail_qty <= 0:
                    p_idx += 1
                    continue

                deduct_qty = min(avail_qty, remaining_qty)
                purchase_df.loc[batch.name, '剩余库存'] -= deduct_qty
                stock.loc[batch.name, '剩余库存'] -= deduct_qty

                record = dict(sale_data)
                record['采购批次号'] = batch['入库批次号']
                record['扣减数量'] = deduct_qty
                record['采购成本'] = deduct_qty * batch['含税单价']
                record['缺货数量'] = 0
                deduct_records.append(record)

                remaining_qty -= deduct_qty
                if stock.loc[batch.name, '剩余库存'] <= 0:
                    p_idx += 1

            if remaining_qty > 0:
                record = dict(sale_data)
                record['采购批次号'] = ''
                record['扣减数量'] = 0
                record['采购成本'] = 0
                record['缺货数量'] = remaining_qty
                deduct_records.append(record)

    deduct_df = pd.DataFrame(deduct_records)
    return deduct_df
