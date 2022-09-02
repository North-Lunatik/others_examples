from dataclasses import dataclass
import os
from pathlib import Path
from tkinter.font import families
from openpyxl import load_workbook
from datetime import datetime 
from typing import Dict, Optional
from progressbar import ProgressBar

from gb2_local.api.promed import Task
from gb2_local.db.mysql import get_vgb2db


@dataclass
class PersonData:
    fam: str
    im: str
    ot: str
    birth_date: datetime
    enp: str


class AdditionalDataGetter(Task):
    """Класс для получения дополнительных данных из API."""

    def __init__(self):
        """Конструктор класса."""
        super().__init__()
        self.external_data = None

    def load_data_from_excel(self, fpath: Path) -> None:
        """Получаем содержимое активного листа документа xlsx."""
        rows_data = []
        wb = load_workbook(str(fpath))
        ws = wb.active
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

        self.external_data = rows_data

    def get_prepared_data(self) -> dict:
        """Получаем обработанные данные."""
        return self.external_data

    GET_PERSON_DATA = "/api/Person"
    GET_REFBOOK = "/api/Refbook"
    GET_ADDRESS = "/api/Address"

    def get_address(self, api, people_id: str, address_id: str) -> dict:
        """Возвращает части запрашиваемого адреса."""
        response = api.get_request_data(self.GET_ADDRESS, {
            "Person_id": people_id,
            "Address_id": address_id,
        })
        data = response.json()
        data = data.get('data')
        if data:
            if isinstance(data, dict):
                data = list(data.values())[0]
            else:
                data = data[0]

            address_full = data.get("Address_Address")
            street_id = data.get("KLStreet_id")
            house = data.get("Address_House")
            corpus = data.get("Address_Corpus")

            response = api.get_request_data(self.GET_REFBOOK, {"Refbook_TableName": "dbo.KLStreet", "id": street_id})
            adr_data = response.json()
            adr_data = adr_data.get('data')
            street_name = adr_data[0].get("Name")

            return {'address_full': address_full, 'street_name': street_name, 'house': house, 'corpus': corpus}
        return {}

    def get_attachment_state(self, live_address: dict, reg_address: dict) -> Optional[tuple]:
        """Возвращет номер участка."""

        def check_in_db(street:str, house: str, build: Optional[str] = None) -> str:
            result = ''
            try:
                conn, cur = get_vgb2db()
                sql = ''
                if build:
                    sql = f"SELECT DISTINCT uchastok FROM gb2_territory WHERE ul LIKE '%{street.upper()}' AND dom LIKE '{house}' AND kor LIKE '{build.upper()}'"
                else:
                    sql = f"SELECT DISTINCT uchastok FROM gb2_territory WHERE ul LIKE '%{street.upper()}' AND dom LIKE '{house}' AND kor IS NULL"
                
                if sql:
                    cur.execute(sql)
                    res = cur.fetchone()
                    if res:
                        result = res[0]
            except Exception as e:
                print(e)
            finally:
                if cur is not None:
                    cur.close()
                if conn is not None and conn.open == 1:
                    conn.close()
            
            return result

        state = ''
        if live_address:
            if live_address.get('corpus'):
                state = check_in_db(live_address['street_name'], live_address['house'], build=live_address['corpus'])
            else:
                state = check_in_db(live_address['street_name'], live_address['house'])

        if not state and reg_address:
            if reg_address.get('corpus'):
                state = check_in_db(reg_address['street_name'], reg_address['house'], build=reg_address['corpus'])
            else:
                state = check_in_db(reg_address['street_name'], reg_address['house'])

        return state

    def get_person_data(self, api, people_data: PersonData) -> dict:
        """Возвращает адрес(-а) и контактные данные."""
        # получаем данные по персоналке
        response = api.get_request_data(self.GET_PERSON_DATA, {
            "PersonSurName_SurName": people_data.fam,
            "PersonFirName_FirName": people_data.im,
            "PersonSecName_SecName": people_data.ot,
            "PersonBirthDay_BirthDay": people_data.birth_date.strftime('%Y-%m-%d'),
            "Polis_Num": people_data.enp,
        })
        data = response.json()
        data = data.get('data')
        if data:
            data = data[0]
            adr_reg_id = data.get("UAddress_id")
            adr_live_id = data.get("PAddress_id")
            ppl_id = data.get("Person_id")

            registration_address = self.get_address(api, ppl_id, adr_reg_id)
            live_address = self.get_address(api, ppl_id, adr_live_id)
            state = self.get_attachment_state(live_address, registration_address)

            return {
                'adr_reg': registration_address.get('address_full', ''),
                'adr_live': live_address.get('address_full', ''),
                'state': state or '',
            }
        return {}

    def exec_task(self, api_obj, DEBUG_MODE=False):
        """Логика задачи."""
        bar = ProgressBar(min_value=0, max_value=len(self.external_data))
        bar.start()
        for i, data in enumerate(self.external_data):
            pd = PersonData(
                    fam=data.get('FAM'),
                    im=data.get('IM'),
                    ot=data.get('OT'),
                    birth_date=data.get('DR'),
                    enp=data.get('ENP')
                )
            person_data = self.get_person_data(api_obj, pd)

            data['address_of_registration'] = person_data.get('adr_reg', '')
            data['address_of_live'] = person_data.get('adr_live', '')
            data['state'] = person_data.get('state', '')
            bar.update(i)
        bar.finish()


if __name__ == "__main__":
    fname = Path(os.getcwd()) / 'assets' / 'finish.xlsx'
    task = AdditionalDataGetter()
    task.load_data_from_excel(fname)
    task.start()
    a = task.get_prepared_data()
