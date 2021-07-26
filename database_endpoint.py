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


app = Flask(__name__)

#These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(DBSession) #g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()

"""
-------- Helper methods (feel free to add your own!) -------
"""

def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    print("log")
    log = Log(message=json.dumps(d['payload']))
    g.session.add(log)    
    g.session.commit()

class DataStore():
    payload = None
    sig = None
    pk = None
    platform = None

data = DataStore()




"""
---------------- Endpoints ----------------
"""
    
@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True


        payload = content["payload"]
        data.payload = json.dumps(payload)
        data.sig = content["sig"]
        data.pk = payload["sender_pk"]
        data.platform = payload["platform"]
 
        if data.platform == "Ethereum":
            eth_encoded_msg = eth_account.messages.encode_defunct(text=data.payload)

            if eth_account.Account.recover_message(eth_encoded_msg,signature=data.sig) == data.pk:
                pass
            else:
                error = True

        elif data.platform  == "Algorand":

            if algosdk.util.verify_bytes(data.payload.encode('utf-8'),data.sig, data.pk):
                pass
            else:
                error = True

        else:
            error = True

        if error:
            print( json.dumps(content) )
            log_message(content)
            return jsonify( False )

        else:

            order = content['payload']
            del order['platform']
            order['signature']=content['sig']
            new_order = Order(**order)
            g.session.add(new_order)    
            g.session.commit()
            return  jsonify(True)




@app.route('/order_book')
def order_book():
    #Your code here
    #Note that you can access the database session using g.session
    result = {}
    orders = g.session.execute('SELECT * FROM orders')
    order_data = {}
    order_array = []

    counter = 0

    for order in orders:
        order_data['sender_pk'] = order.sender_pk
        order_data['receiver_pk'] = order.receiver_pk
        order_data['buy_currency'] = order.buy_currency
        order_data['sell_currency'] = order.sell_currency
        order_data['buy_amount'] = order.buy_amount
        order_data['sell_amount'] = order.sell_amount
        order_data['signature'] = order.signature
        order_array.append(order_data)
        counter+=1

    result['data'] = order_array 
    print(counter)   
    return jsonify(result)

@app.route('/log')
def logs():
    result = {}
    logs = g.session.execute('SELECT * FROM log')
    log_data = {}
    log_array = []

    for log in logs:
        log_data['id'] = log.id
        log_data['logtime'] = log.logtime
        log_data['message'] = log.message
        log_array.append(log_data)

    result['logs'] = log_array 
    return jsonify(result)

if __name__ == '__main__':
    app.run(port='5002')

