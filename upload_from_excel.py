import os
from pathlib import Path
from gb2_local.db.mysql import get_vgb2db
from openpyxl import load_workbook
from datetime import datetime 


fname = Path(os.getcwd()) / 'assets' / 'finish.xlsx'

# получаем данные из документа
wb = load_workbook(str(fname))
ws = wb.active

rows_data = []
for i, row in enumerate(ws.rows):
    if i == 0:
        header = []
        for cell in row:
           header.append(cell.value)

    if i > 0:
        buf = {}
        for j, cell in enumerate(row):
           buf[header[j]] = cell.value
        rows_data.append(buf)

# пишем данные в таблицу
try:
    conn, cur = get_vgb2db()

    for item in rows_data:
        sql = f'''
        INSERT INTO ne_prikreplennie (fam, im, ot, dr, enp, datez, id_pac) 
        VALUES(
            '{item["FAM"]}',
            '{item["IM"]}',
            '{"NULL" if item["OT"] in (None, "") else item["OT"]}',
            '{item["DR"]}',
            '{item["ENP"]}',
            '{datetime.strftime(datetime.now(), "%Y-%m-%d")}',
            {item["ID_PAC"]}
            )
        '''
        cur.execute(sql.replace('\n', '').replace('  ', ''))
    conn.commit()
except Exception as e:
    print(e)
finally:
    if cur is not None:
        cur.close()
    if conn is not None and conn.open == 1:
        conn.close()

