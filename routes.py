from flask import Flask, request, jsonify
from app import app
from models import db, User, Group, Expense
from sqlalchemy import text
import json
from datetime import datetime

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'message': 'Name is required'}), 400
    
    new_user = User(name=name)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@app.route('/groups', methods=['POST'])
def create_group():
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


@app.route('/groups', methods=['GET'])
def get_groups():
    groups = Group.query.all()
    return jsonify([group.to_dict() for group in groups])


@app.route('/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    return jsonify(group.to_dict())



@app.route('/expenses', methods=['POST'])
def add_expense():
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
        return jsonify({'message': 'Group not found'}), 404
    payer = User.query.get(payer_id)
    if not payer:
        return jsonify({'message': 'Payer not found'}), 404

    new_expense = Expense(description = description, amount = amount, group_id = group_id, payer_id = payer_id, split_type = split_type, split_data = split_data)

    db.session.add(new_expense)
    db.session.commit()
    return jsonify({'message': 'Expense added successfully', 'expense': new_expense.to_dict()}), 201

@app.route('/expenses', methods=['GET'])
def get_expenses():
  expenses = Expense.query.all()
  return jsonify([expense.to_dict() for expense in expenses])


@app.route('/groups/<int:group_id>/balances', methods=['GET'])
def get_group_balances(group_id):
    group = Group.query.get(group_id)
    if not group:
         return jsonify({'message': 'Group not found'}), 404
    
    users = group.users
    balances = {user.id: 0 for user in users}
    
    for expense in group.expenses:
          if expense.split_type == 'equal':
            split_amount = expense.amount / len(users)
            for user in users:
                if user.id == expense.payer_id:
                   balances[user.id] += expense.amount - split_amount #payer gets full amount but has to pay his share
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