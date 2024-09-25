import psycopg2
from flask import Flask,request,jsonify
from os import urandom
from regex import fullmatch
import time


db = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS tokens(uuid TEXT PRIMARY KEY,token TEXT NOT NULL,timestamp INTEGER)")
db.commit()
app = Flask(__name__)

@app.route("/genNewToken/<uuid>",methods=['GET','POST'])
def genNewToken(uuid):
    if request.method != "POST":
        return "Forbidden", 400
    if not isUUID(uuid):
        return "Invalid UUID", 417
    newToken = str(int.from_bytes(urandom(16),"little"))
    tmp_db = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
    cur = tmp_db.cursor()
    if not exists(uuid):
        cur.execute(f"INSERT INTO tokens VALUES ('{uuid}','{newToken}',{int(time.time())})")
    else:
        cur.execute(f"UPDATE tokens SET token = '{newToken}' WHERE uuid = '{uuid}'")
    cur.execute(f"DELETE FROM tokens WHERE timestamp < {int(time.time()-72000)}")
    tmp_db.commit()
    cur.close()
    tmp_db.close()
    return "Token generated successfully!", 200

@app.route("/getToken/<uuid>",methods=['GET','POST'])
def getToken(uuid):
    if not isUUID(uuid):
        return "Invalid UUID", 417
    token = exists(uuid)
    if not token:
        return "Not Found", 404
    return jsonify(token[0])
    
def isUUID(uuid):
    if fullmatch("^[0-9a-fA-F]{8}\\-[0-9a-fA-F]{4}\\-[0-9a-fA-F]{4}\\-[0-9a-fA-F]{4}\\-[0-9a-fA-F]{12}$",uuid) == None:
        return False
    return True

def exists(uuid):
    tmp_db = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
    cur = tmp_db.cursor()
    cur.execute(f"SELECT token FROM tokens WHERE uuid = '{uuid}'")
    token = cur.fetchall()
    if len(token) == 0:
        return False
    else:
        return token
