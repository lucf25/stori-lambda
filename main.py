from crypt import methods
import json
from flask import Flask, render_template, request, send_file, Response
import pandas as pd
import statistics
import numpy as np
from random import randint, random, choice
import string, json, os
from flask_mail import Mail, Message
import boto3
import io


from sqlalchemy import create_engine, insert
app = Flask(__name__)

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/fireEmail", methods=["POST"])
def generatemail():
    req = request.get_json()
    s3 = getAWSClient()
    obj = s3.get_object(Bucket='stori-data', Key=req["filename"])


    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    df[['Month','Day']] = df["Date"].str.split("/", 1, expand=True);
    df = df.astype({'Month':'int'})

    df['Type'] = np.where(df["Transaction"] > 0 , "Credit", "Debit")

    balance_month = df.groupby("Month")["Transaction"].count()
    balance = df["Transaction"].sum()
    average_credit =  df.groupby(["Month", "Type"])["Transaction"].mean().reset_index()
    #return average_credit.to_dict()
    sendEmail( render_template("summary.html", total_balance=round(balance, 2), balance_month=balance_month.to_dict(), average_credit=average_credit.to_html(index=False, classes=["table-email"]) ), req["email"])
    return df.to_dict();


@app.route("/generateCSV")
def generateRandomData():
    y = randint(1, 100)
    random_list = []
    for x in range(y):
        random_list.append([x, str(randint(1,12))+"/"+""+str(randint(1,28)), round(choice([-1,1])*random() *100, 2)])        
    #engine = create_engine("mysql+mysqldb://admin:"+'cehxuk-paxqec-sowHo3'+"@database-1.ctwyx4gwfp3n.us-east-1.rds.amazonaws.com/stori")
    ls = pd.DataFrame(random_list, columns=["Id", "Date", "Transaction"])
    filename = get_random_string(30)+".csv"
    s3 = getAWSClient()
    object = s3.put_object(Body=ls.to_csv(index=False), Bucket='stori-data', Key=filename)

    
    csv_id = 0
    #with engine.connect() as connection: 
    #    id = connection.execute(f"INSERT INTO csv (filename, transactions) VALUES ('{filename}', {y})  ")
    #    csv_id = id.lastrowid
    #ls["csv_id"] = csv_id
    
    #ls.to_sql("Transactions",con=engine,index=False, if_exists="append" )

    response = {"Transactions": y,  "Filename": filename} 
    return json.dumps(response)

@app.route("/getCSVList")
def getCSVList():

    s3 = getAWSClient()
    csvs = s3.list_objects_v2(
        Bucket="stori-data",
    )
    cr = []
    for content in csvs.get('Contents', []):
        cr.append(content["Key"])

    return (cr)

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(choice(letters) for i in range(length))
    return result_str


@app.route("/email")
def sendEmail(html, email):
    app.config['MAIL_SERVER']='smtp-relay.sendinblue.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'luisenriquecfr@me.com'
    app.config['MAIL_PASSWORD'] = 'OKUFA5MzBpW64Qjv'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = False
    mail = Mail(app)

    msg = Message('Stori Account Summary', sender = 'dev@dogker.xyz', recipients = [email])
    msg.body = "This is the email body"
    msg.html = html
    mail.send(msg) 
    return "Sent"

@app.route("/downloadCSV/<path:filename>")
def downloadCSV(filename): 
    s3 = getAWSClient()
    obj = s3.get_object(Bucket='stori-data', Key=filename)
    return Response(
        obj['Body'].read(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename="+filename}
    )
    


def getAWSClient():
    client = boto3.client('s3',
    aws_access_key_id="AKIAQT5FHBS2FKWU2LNG",
    aws_secret_access_key="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",
    )
    return client

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
