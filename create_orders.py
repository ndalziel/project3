from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
import random

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#Clear tables
session.query(Order).delete()
session.commit()

def create_order(platform):
    platforms = ["Algorand", "Ethereum"]       
    assert platform in platforms
    other_platform = platforms[1-platforms.index(platform)]
    order = {}
    order['buy_currency'] = other_platform
    order['sell_currency'] = platform
    order['buy_amount'] = random.randint(1,10)
    order['sell_amount'] = random.randint(1,10)
    order['sender_pk'] = hex(random.randint(0,2**256))[2:] 
    order['receiver_pk'] = hex(random.randint(0,2**256))[2:] 

    return order


def create_orders(n):

    for i in range(n):
        platforms = ["Algorand", "Ethereum"]
        platform = platforms[random.randint(0,1)] 
        order = create_order(platform)
        new_order = Order(**order)
        session.add(new_order)    
        session.commit()

create_orders(2)