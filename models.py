from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
