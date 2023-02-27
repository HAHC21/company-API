# System Libraries
import os
import uuid
import datetime
import pandas
import time

# Flask libraries
from flask import Flask, request
from flask_mongoengine import MongoEngine
from flask_cors import CORS
from mongoengine.errors import NotUniqueError, ValidationError

##################
#
# App Configuration
#
##################

# Basic startup configuration
app = Flask(__name__, static_folder='static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MONGODB_SETTINGS'] = {
    'db': 'test',
    'host': '',
    'port': 27017,
}
CORS(app)


# Current salary
current_minimum_wage = 1300000


# Initialize database
db = MongoEngine(app)


# Database Models
class Company(db.Document):
    NIT = db.StringField(unique=True)
    verification_digit = db.IntField()
    name = db.StringField(max_length=256)
    address = db.StringField(max_length=256)

    def as_dict(self):
        return {
            "NIT": self.NIT,
            "name": self.name,
            "address": self.address
        }


class Employee(db.Document):
    identification = db.IntField(unique=True)
    name = db.StringField()
    salary = db.FloatField()
    hiring_date = db.DateField()
    birthdate = db.DateField()
    company = db.ReferenceField(Company)
    current_loans = db.IntField()

    def as_dict(self):
        return {
            'identification': self.identification,
            'name': self.name,
            'salary': self.salary,
            'hiring_date': self.hiring_date,
            'birthdate': self.birthdate,
            'company': self.company.as_dict() if self.company else None,
            'current_loans': self.current_loans,
        }


class Loan(db.Document):
    value = db.FloatField()
    installments = db.IntField()
    installments_paid = db.IntField()
    total_paid = db.FloatField(default=0)
    total_left = db.FloatField()
    start_date = db.DateField()
    end_date = db.DateField()
    employee = db.ReferenceField(Employee)

    def as_dict(self):
        return {
            'id': str(self.id),
            'value': self.value,
            'installments': self.installments,
            'installments_paid': self.installments_paid,
            'total_paid': self.total_paid,
            'payable_amount': self.total_left,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'employee': self.employee.as_dict()
        }
    
    def simple_dict(self):
        return {
            'id': str(self.id),
            'value': self.value,
            'installments': self.installments,
            'installments_paid': self.installments_paid,
            'total_paid': self.total_paid,
            'payable_amount': self.total_left,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }

## Support Functions
def generate_vd(NIT):
        # Add up odd numbers
        odds = 0
        for i in [0, 2, 4, 6, 8]:
            odds = odds + int(NIT[i])
        
        odds = odds * 3
        
        evens = 0
        for i in [1, 3, 5, 7]:
            evens = evens + int(NIT[i])
        
        total = odds + evens
        vd = 0
        found = False

        while not found:
            if (total + vd) % 10 == 0:
                found = True
                return vd
            else:
                vd = vd + 1


def calculate_age(birthdate):
    if not isinstance(birthdate, datetime.date):
        birthdate = datetime.datetime.strptime(birthdate, '%Y/%m/%d')
    else:
        birthdate = datetime.datetime(birthdate.year, birthdate.month, birthdate.day)
    now = datetime.datetime.now()
    age = now - birthdate
    age = age.days / 360

    return age


def calculate_salary(hiring_date):
    hiring_date = datetime.datetime.strptime(hiring_date, '%Y/%m/%d')
    now = datetime.datetime.now()
    working_age = now - hiring_date
    working_age = working_age.days / 360
    working_age = int(working_age)

    # new employees cannot earn less than minimum wage
    if working_age < 6:
        working_age = 6

    salary = (working_age * current_minimum_wage) / 6

    return salary


def validate_employee(employee_data):
    identification = employee_data.get('identification', False)
    salary =  employee_data.get('salary', False)
    hiring_date =  employee_data.get('hiring_date', False)
    birthdate =  employee_data.get('birthdate', False)

    try:
        identification = int(identification)
    
    except Exception:
        return {
            'result': 'Employee identification not valid.'
        }, 500 

    try:
        salary = float(salary)
    
    except Exception:
        return {
            'result': 'Employee salary not valid.'
        }, 500 

    # Dates must be in format YYYY/MM/DD
    
    try:
        hiring_date = datetime.datetime.strptime(hiring_date, '%Y/%m/%d')
    
    except Exception:
        return {
            'result': 'Employee hiring date not valid.'
        }, 500
    
    try:
        birthdate = datetime.datetime.strptime(birthdate, '%Y/%m/%d')
    
    except Exception:
        return {
            'result': 'Employee birth date not valid.'
        }, 500


## API Endpoints

#####
#
# Company Endpoints
#
#####

# Endpoint to get data for all companies
@app.route('/companies/', methods=['GET'])
def list_companies():
    
    try:
        companies_data = Company.objects.all()
        companies = [company.as_dict() for company in companies_data]

        return {
            'result': 'success',
            'companies': companies
        }, 200
    
    except Exception:
        return {
            'result': 'An error has occured.'
        }, 500


# Endpoint to get / update company information
@app.route('/company/<nit>', methods=['GET', 'POST'])
@app.route('/company/<nit>/', methods=['GET', 'POST'])
def company(nit):

    # Read
    if request.method == 'GET':
        # Search NIT in database
        result = Company.objects.filter(NIT=str(nit)).first()

        # Return results accordingly
        if result:
            print(result.as_dict())
            return {
                'result': 'success',
                'company': result.as_dict()
            }, 200

        else:
            return {
                'result': 'Error: Company ID is not in the database.'
            }, 400

    # Update
    else:
        company = Company.objects.filter(NIT=str(nit)).first()

        if company:
            company_data = request.get_json()
            
            # Update company information
            try:
                nit = company_data.get('NIT', False)
                company.NIT = nit if nit else company.NIT

                name = company_data.get('name', False)
                company.name = name if name else company.name

                address = company_data.get('address', False)
                company.address = address if address else company.address

                company.save()

                return {
                    'result': 'Company information updated successfully.',
                    'company_data': company.as_dict()
                }, 200
            
            except ValidationError:
                return {
                    'result': 'Error: Employee data not valid.'
                }, 500

            except Exception as err:
                print(err)
                return {
                    'result': 'Error: Could not update company information.'
                }, 500

        else:
            return {
                'result': 'Error: Company ID is not in the database.'
            }, 400


# Endpoint to create a new company
@app.route('/company/', methods=['POST'])
def new_company():

    if request.get_json():
        company_data = request.get_json()
    else:
        return {
            'result': 'Error: Company data not received.'
        }, 400

    # Check if data was sent
    if not company_data:
        return {
            'result': 'Error: Company data not received.'
        }, 400

    else:
        try:
            # Calculate validation digit
            verification_digit = generate_vd(company_data.get('NIT', False))
            company_data['verification_digit'] = verification_digit

            # Save
            company = Company(**company_data)
            company.save()

            return {
                'result': 'success',
                'company_data': company.as_dict()
            }, 200

        except NotUniqueError:
            return {
                'result': 'Error: A company with the provided NIT already exists.'
            }, 400

        except Exception as err:
            print(err)
            return {
                'result': 'Error: Company could not be saved in the database.'
            }, 500


# Endpoint to delete a company
@app.route('/company/<int:nit>/delete', methods=['POST'])
def delete_company(nit):

    # Search NIT in database
    result = Company.objects.filter(NIT=str(nit)).first() 

    # Perform deletion as requested
    if result:
        try:
            result.delete()
            return {
                'result': 'Company deleted successfully.',
            }, 200
        
        except Exception as err:
            print(err)
            return {
                'result': 'Error: Could not delete company information.'
            }, 500

    else:
        return {
            'result': 'Error: Company ID is not in the database.'
        }, 400


#####
#
# Employee Endpoints
#
#####

# Endpoint to get data for all employees
@app.route('/employees/', methods=['GET'])
def list_employees():
    
    try:
        employee_data = Employee.objects.all()
        employees = [employee.as_dict() for employee in employee_data]

        print(employees)

        return {
            'result': 'success',
            'employees': employees
        }, 200
    
    except Exception:
        return {
            'result': 'An error has occurred.'
        }, 500


# Read / Update employee
@app.route('/employee/<int:id>', methods=['GET', 'POST'])
def employee(id):

    # Read
    if request.method == 'GET':
        # Search NIT in database
        result = Employee.objects.filter(identification=id).first()

        # Return results accordingly
        if result:
            return result.as_dict()

        else:
            return {
                'result': 'Error: Employee ID is not in the database.'
            }, 400

    # Update
    else:
        employee = Employee.objects.filter(identification=id).first()

        if employee:
            employee_data = request.json.get('data', False)
            
            # Update employee information
            try:
                # Validate data
                validate_employee(employee_data)

                identification = employee_data.get('identification', False)               
                employee.identification = identification if identification else employee.identification

                name =  employee_data.get('name', False)
                employee.name = name if name else employee.name

                salary = calculate_salary(employee_data.get('hiring_date'))
                employee.salary = salary

                # Dates must be in format YYYY/MM/DD
                hiring_date =  employee_data.get('hiring_date', False)                
                employee.hiring_date = hiring_date if hiring_date else employee.hiring_date

                birthdate =  employee_data.get('birthdate', False)
                employee.birthdate = birthdate if birthdate else employee.birthdate

                employee.save()

                return {
                    'result': 'Employee information updated successfully.',
                    'employee_data': employee.as_dict()
                }, 200
            
            except ValidationError:
                return {
                    'result': 'Error: Employee data not valid.'
                }, 500

            except NotUniqueError:
                return {
                    'result': 'Employee ID already exists in the database.'
                }, 200

            except Exception as err:
                print(err)
                return {
                    'result': 'Error: Could not update employee information.'
                }, 500

        else:
            return {
                'result': 'Error: Employee ID is not in the database.'
            }, 400



# Endpoint to create a new employee
@app.route('/employee/', methods=['POST'])
def new_employee():

    print(request.get_json()) # debug
    if request.get_json():
        employee_data = request.get_json()['data']
    else:
        return {
            'result': 'Error: Employee data not received.'
        }, 400

    # Check if data was sent
    if not employee_data:
        return {
            'result': 'Error: Employee data not received.'
        }, 400

    else:
        try:
            validate_employee(employee_data)

            company = Company.objects.filter(NIT=employee_data.get('company')).first()
            if company:
                employee_data['company'] = company
            else:
                employee_data['company'] = None
            
            # Calculate salary
            employee_data['salary'] = calculate_salary(employee_data.get('hiring_date'))
            
            # Default value for current_loans
            employee_data['current_loans'] = 0

            # Validate age
            age = calculate_age(employee_data.get('birthdate'))

            if age > 70:
                return {
                    'result': 'Error: Employee exceeds maximum allowed age.'
                }, 400
            elif age < 18:
                return {
                    'result': 'Error: Employee is below minimum allowed age.'
                }, 400

            # Create and save
            employee = Employee(**employee_data)
            employee.save()

            return {
                'result': 'Employee created successfully.',
                'employee_data': employee.as_dict()
            }, 200

        except NotUniqueError:
            return {
                'result': 'Error: An employee with the provided ID already exists.'
            }, 400

        except Exception as err:
            print(err)
            return {
                'result': 'Error: Employee could not be saved in the database.'
            }, 500


# Endpoint to delete a employee
@app.route('/employee/<int:identification>/delete', methods=['POST'])
def delete_employee(identification):

    # Search NIT in database
    result = Employee.objects.filter(identification=identification).first() 

    # Perform deletion as requested
    if result:
        try:
            result.delete()
            return {
                'result': 'Employee deleted successfully.',
            }, 200
        
        except Exception as err:
            print(err)
            return {
                'result': 'Error: Could not delete employee information.'
            }, 500

    else:
        return {
            'result': 'Error: Employee ID is not in the database.'
        }, 400


# Endpoint for employee company
@app.route('/employee/<int:identification>/company', methods=['GET'])
def employee_company(identification):

    # Search NIT in database
    employee = Employee.objects.filter(identification=identification).first() 

    # Perform deletion as requested
    if employee:
        if employee.company:
            return {
                    'company': employee.company.as_dict(),
                }, 200
        
        else:
            return {
                'result': 'Error: Employee not registered to any company.'
            }, 400

    else:
        return {
            'result': 'Error: Employee ID is not in the database.'
        }, 400


# Endpoint for employee age
@app.route('/employee/<int:identification>/age', methods=['GET'])
def employee_age(identification):

    # Search NIT in database
    employee = Employee.objects.filter(identification=identification).first() 

    # Perform deletion as requested
    if employee:
        age = calculate_age(employee.birthdate)

        return {
            'age': int(age)
        }

    else:
        return {
            'result': 'Error: Employee ID is not in the database.'
        }, 400


# Endpoint for employee loans
@app.route('/employee/<int:identification>/loans', methods=['GET'])
def employee_loans(identification):

    # Search NIT in database
    employee = Employee.objects.filter(identification=identification).first()

    # Perform deletion as requested
    if employee:
        loans = Loan.objects.filter(employee=employee)

        results = []

        for loan in loans:
            results.append(loan.simple_dict())

        return {
            'result': results
        }

    else:
        return {
            'result': 'Error: Employee ID is not in the database.'
        }, 400


#####
#
# Loan Endpoints
#
#####

# Endpoint to get data for all loans
@app.route('/loans/', methods=['GET'])
def list_loans():
    
    try:
        loans_data = Loan.objects.all()
        loans = [loan.as_dict() for loan in loans_data]

        return {
            'result': 'success',
            'loans': loans
        }, 200
    
    except Exception:
        return {
            'result': 'An error has occurred.'
        }, 500

# Read and update loans
@app.route('/loan/<id>', methods=['GET', 'POST'])
def loan_data(id):
    # Read
    if request.method == 'GET':
        # Search NIT in database
        try:
            result = Loan.objects.filter(id=id).first()

            # Return results accordingly
            if result:
                return result.as_dict()

            else:
                return {
                    'result': 'Error: Loan does not exist in the database.'
                }, 400
        
        except ValidationError:
            return {
                    'result': 'Error: Loan ID not valid.'
                }, 400
    
    else:
        try:
            loan = Loan.objects.filter(id=id).first()

            if loan:
                loan_data = request.json.get('data', False)
                installments = loan_data.get('installments')
                amount = loan_data.get('amount')

                if installments:
                    loan.installments_paid = loan.installments_paid + installments
                
                    if amount:
                        loan.total_paid = loan.total_paid + amount
                    else:
                        amount = (loan.value / loan.installments) * installments
                        loan.total_paid = loan.total_paid + amount

                loan.save()

                return {
                    'result': 'Loan updated successfully.',
                    'loan_data': loan.as_dict()
                }, 200

            else:
                return {
                    'result': 'Error: Loan does not exist in the database.'
                }, 400
            
        except Exception as err:
            print(err)
            return {
                'result': 'Error: Could not update loan information.'
            }, 500



# Endpoint to create a new loan
@app.route('/loan/', methods=['POST'])
def new_loan():

    print(request.get_json()) # debug
    if request.get_json():
        loan_data = request.get_json()['data']
    else:
        return {
            'result': 'Error: Employee data not received.'
        }, 400

    # Check if data was sent
    if not loan_data:
        return {
            'result': 'Error: Employee data not received.'
        }, 400

    else:
        employee = loan_data.get('employee')
        employee = Employee.objects.filter(identification=employee).first()
        if not employee:
            return {
                'result': 'Error: Employee does not exist.'
            }, 400
        
        elif employee.current_loans >= 3:
            return {
                'result': 'Error: Employee cannot have more than 3 loans.'
            }, 400
        else:
            now = datetime.datetime.now()

            loan_data['employee'] = employee
            loan_data['installments_paid'] = 0
            loan_data['start_date'] = now
            loan_data['total_left'] = loan_data['value']

            installments = int(loan_data.get('installments'))
            loan_data['end_date'] = now + datetime.timedelta(days=installments * 30)

            loan = Loan(**loan_data)
            loan.save()

            employee.current_loans = employee.current_loans + 1
            employee.save()

            return {
                'result': 'Loan created successfully.',
                'loan_data': loan.as_dict()
            }, 200



# Endpoint to delete a loan
@app.route('/loan/<id>/delete', methods=['POST'])
def delete_loan(id):

    # Search NIT in database
    loan = Loan.objects.filter(id=id).first() 

    # Perform deletion as requested
    if loan:
        try:
            # Update current loans for employee
            employee = Employee.objects.filter(id=loan.employee.id).first()
            employee.current_loans = employee.current_loans - 1
            employee.save()

            loan.delete()

            return {
                'result': 'Loan deleted successfully.',
            }, 200
        
        except Exception as err:
            print(err)
            return {
                'result': 'Error: Could not delete Loan information.'
            }, 500

    else:
        return {
            'result': 'Error: Loan ID is not in the database.'
        }, 400