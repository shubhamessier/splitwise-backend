from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from datetime import datetime
from sqlalchemy import text
import json
from werkzeug.exceptions import NotFound


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    groups = db.relationship('Group', secondary='user_group', back_populates='users')
    expenses = db.relationship('Expense', back_populates='payer')
    
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    users = db.relationship('User', secondary='user_group', back_populates='groups')
    expenses = db.relationship('Expense', back_populates='group')
    
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'users': [user.to_dict() for user in self.users]
        }


user_group = db.Table('user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    group = db.relationship('Group', back_populates='expenses')
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payer = db.relationship('User', back_populates='expenses')
    split_type = db.Column(db.String(20), nullable=False) # 'equal' or 'percentage'
    split_data = db.Column(db.JSON, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self,description, amount, group_id, payer_id, split_type, split_data = None):
        self.description = description
        self.amount = amount
        self.group_id = group_id
        self.payer_id = payer_id
        self.split_type = split_type
        self.split_data = split_data


    def to_dict(self):
       return {
           'id': self.id,
           'description': self.description,
           'amount': self.amount,
           'group_id': self.group_id,
           'payer_id': self.payer_id,
           'split_type': self.split_type,
           'split_data': self.split_data,
           'date_added': self.date_added.isoformat()
       }
#--- End Models ---

# --- Error Handlers ---
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'message': 'Resource not found', 'error': str(error)}), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'message': 'Bad request', 'error': str(error)}), 400

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal server error', 'error': str(error)}), 500
# --- End Error Handlers ---


@app.route('/')
def home():
    return "Hello, World!"


# --- Routes ---
@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({'message': 'Name is required'}), 400
        
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201
    except Exception as e:
         db.session.rollback()
         return internal_server_error(e)

@app.route('/users', methods=['GET'])
def get_users():
     try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])
     except Exception as e:
         return internal_server_error(e)

@app.route('/groups', methods=['POST'])
def create_group():
    try:
        data = request.get_json()
        name = data.get('name')
        user_ids = data.get('user_ids')
        if not name:
            return jsonify({'message': 'Group name is required'}), 400
        if not user_ids:
            return jsonify({'message': 'User IDs are required'}), 400
        
        new_group = Group(name=name)
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                new_group.users.append(user)
            else:
                return jsonify({'message': f'User with id {user_id} not found'}), 404
        
        db.session.add(new_group)
        db.session.commit()
        return jsonify({'message': 'Group created successfully', 'group': new_group.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return internal_server_error(e)

@app.route('/groups', methods=['GET'])
def get_groups():
    try:
        groups = Group.query.all()
        return jsonify([group.to_dict() for group in groups])
    except Exception as e:
          return internal_server_error(e)

@app.route('/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
    try:
        group = Group.query.get(group_id)
        if not group:
            raise NotFound(f"Group with id {group_id} not found")
        return jsonify(group.to_dict())
    except NotFound as e:
          return not_found_error(e)
    except Exception as e:
        return internal_server_error(e)

@app.route('/expenses', methods=['POST'])
def add_expense():
    try:
        data = request.get_json()
        description = data.get('description')
        amount = data.get('amount')
        group_id = data.get('group_id')
        payer_id = data.get('payer_id')
        split_type = data.get('split_type')
        split_data = data.get('split_data')

        if not description or not amount or not group_id or not payer_id or not split_type:
             return jsonify({'message': 'Missing required expense data'}), 400
        if split_type not in ('equal', 'percentage'):
             return jsonify({'message': 'Invalid split type'}), 400
        
        if split_type == 'percentage' and not split_data:
             return jsonify({'message': 'split data required for percentage split'}), 400
        
        group = Group.query.get(group_id)
        if not group:
             return not_found_error(f'Group with id {group_id} not found')
        payer = User.query.get(payer_id)
        if not payer:
            return not_found_error(f'Payer with id {payer_id} not found')
        
        new_expense = Expense(description = description, amount = amount, group_id = group_id, payer_id = payer_id, split_type = split_type, split_data = split_data)

        db.session.add(new_expense)
        db.session.commit()
        return jsonify({'message': 'Expense added successfully', 'expense': new_expense.to_dict()}), 201
    except Exception as e:
          db.session.rollback()
          return internal_server_error(e)

@app.route('/expenses', methods=['GET'])
def get_expenses():
    try:
        expenses = Expense.query.all()
        return jsonify([expense.to_dict() for expense in expenses])
    except Exception as e:
        return internal_server_error(e)


@app.route('/groups/<int:group_id>/balances', methods=['GET'])
def get_group_balances(group_id):
    try:
        group = Group.query.get(group_id)
        if not group:
            raise NotFound(f"Group with id {group_id} not found")
        
        users = group.users
        balances = {user.id: 0 for user in users}
        
        for expense in group.expenses:
            if expense.split_type == 'equal':
                split_amount = expense.amount / len(users)
                for user in users:
                    if user.id == expense.payer_id:
                        balances[user.id] += expense.amount - split_amount
                    else:
                        balances[user.id] -= split_amount
                
            elif expense.split_type == 'percentage':
                for user_id,percentage in expense.split_data.items():
                    user = next((user for user in users if user.id == int(user_id)), None)
                    if user:
                        amount_owed = (percentage/100) * expense.amount
                        if user.id == expense.payer_id:
                            balances[user.id] += expense.amount - amount_owed
                        else:
                            balances[user.id] -= amount_owed
        
        return jsonify({'balances': balances})
    except NotFound as e:
        return not_found_error(e)
    except Exception as e:
         return internal_server_error(e)
# --- End Routes ---


if __name__ == '__main__':
    with app.app_context():
        print("Attempting to create database tables...")
        db.create_all()
        print("Database tables created (or already existed).")

    app.run(debug=True)