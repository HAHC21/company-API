import requests
from bs4 import BeautifulSoup as bs
import random
import datetime
import time
from inputs import names, companies
import json

def generate_names():
    namesl = []
    for i in range(250):
        response = requests.get('https://generadordenombres.online/')
        soup = bs(response.text, 'html.parser')
        name = soup.find('span', {'id': 'resultadoGenerado'})
        name = str(name.text).strip()
        namesl.append(name)
        print(name)

    print(namesl)


def get_random_birthdate():
    day = random.randint(1, 30)
    month = random.randint(1, 12)
    year = random.randint(1980, 1995)

    if month == 2:
        if day > 28:
            day = 28
    
    if month < 10:
        month = f'0{month}'

    if day < 10:
        day = f'0{day}'

    birthdate = f'{year}/{month}/{day}' ##datetime.datetime(year, month, day)

    return birthdate


def get_random_hiring_date():
    day = random.randint(1, 30)
    month = random.randint(1, 12)
    year = random.randint(2005, 2022)

    if month == 2:
        if day > 28:
            day = 28
    
    if month < 10:
        month = f'0{month}'

    if day < 10:
        day = f'0{day}'

    hiring_date =  f'{year}/{month}/{day}' ##datetime.datetime(year, month, day)

    return hiring_date

# from employees import populate_employees
# populate_employees
def populate_employees():
    ids = []
    headers = {
            'Content-Type': 'application/json'
        }

    for i in range(len(names)):
        identification = random.randint(1000000000, 1130000000)

        passed = True
        while passed:
            if identification not in ids:
                ids.append(identification)
                passed = False
            else:
                identification = random.randint(1000000000, 1130000000)

        data = {
            "data": {
                "identification": identification,
                "name": names[i],
                "hiring_date": get_random_hiring_date(),
                "birthdate": get_random_birthdate(),
                "company": companies[i],
            }
        }

        response = requests.post(
            url='http://127.0.0.1:5000/employee/',
            data=json.dumps(data),
            headers=headers
        )

        print(response.content)
