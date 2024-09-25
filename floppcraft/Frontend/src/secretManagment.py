from random import randbytes,seed
from requests import post,get
import uuid as uuidGen
import psycopg2

secretsDB = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
tmp_cur = secretsDB.cursor()
tmp_cur.execute("CREATE TABLE IF NOT EXISTS secrets(uuid TEXT PRIMARY KEY,count INTEGER,sec1 BYTEA,sec2 BYTEA,sec3 BYTEA,sec4 BYTEA,sec5 BYTEA) ")
secretsDB.commit()
tmp_cur.close()
TOKENSERVER = "http://KeyServer:5001"
NUM_SECRETS=5
user_secrets = {}
tmpDB = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
tmp_cur = tmpDB.cursor()
tmp_cur.execute("SELECT * FROM secrets")
data = tmp_cur.fetchall()
for entry in data:
    user_secrets.update({entry[0]:[entry[1],bytes(entry[2]),bytes(entry[3]),bytes(entry[4]),bytes(entry[5]),bytes(entry[6])]})
tmp_cur.close()
tmpDB.close()


def getCount(uuid):
    return user_secrets[uuid][0]

def getSecrets(uuid):
    if not uuid in user_secrets:
        return (-1,-1)
    curSecret = user_secrets[uuid][getCount(uuid)]
    user_secrets[uuid][0] += 1
    if getCount(uuid) > NUM_SECRETS:
        token = getNewToken(uuid)
        genSecrets(uuid,token)
    tmpDB = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
    tmp_cur = tmpDB.cursor()
    tmp_cur.execute(f"UPDATE secrets SET count = {getCount(uuid)} WHERE uuid = '{uuid}'")
    tmpDB.commit()
    tmp_cur.close()
    tmpDB.close()
    newSecret = user_secrets[uuid][getCount(uuid)]
    return (curSecret,newSecret)

def addNewToken():
    uuid = str(uuidGen.uuid4())
    genSecrets(uuid,getNewToken(uuid))
    return (uuid,user_secrets[uuid][1])

def getNewToken(uuid):
    res = post(TOKENSERVER+"/genNewToken/"+uuid)
    if res.status_code != 200:
        return -1
    res = get(TOKENSERVER+"/getToken/"+uuid)
    if res.status_code != 200:
        return -1
    return int(res.text[2:-3])

def genSecrets(uuid,token):
    user_secrets.update({uuid:[1 for _ in range(0,NUM_SECRETS+1)]})
    seed(token)
    for i in range(0,NUM_SECRETS):
        user_secrets[uuid][i+1] = randbytes(8)
    tmpDB = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
    tmp_cur = tmpDB.cursor()
    tmp_cur.execute("INSERT INTO secrets (uuid,count,sec1,sec2,sec3,sec4,sec5) values (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (uuid) DO UPDATE SET count = %s,sec1 = %s,sec2 = %s, sec3 = %s,sec4= %s ,sec5= %s;",(uuid,user_secrets[uuid][0],user_secrets[uuid][1],user_secrets[uuid][2],user_secrets[uuid][3],user_secrets[uuid][4],user_secrets[uuid][5], user_secrets[uuid][0],user_secrets[uuid][1], user_secrets[uuid][2], user_secrets[uuid][3], user_secrets[uuid][4], user_secrets[uuid][5]))
    tmpDB.commit()
    tmp_cur.close()
    tmpDB.close()

