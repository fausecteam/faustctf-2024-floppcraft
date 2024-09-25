import jwt
from flask import Flask, make_response, redirect, render_template,request
from lxml import etree
from io import StringIO
from secretManagment import addNewToken,getSecrets
import psycopg2
import base64
import regex
from PIL import Image
import time
import urllib.request
import io
import os

NUM_IMAGES = 20
MAX_IMAGE_SIZE = 3000000
JWT_ALGO = ["HS256"]
SMALL_REPLACEMENT_IMG = "/9j/4AAQSkZJRgABAQEAAAAAAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wgARCAAeAB4DAREAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAL/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAGQAAAAAAAf/8QAFBABAAAAAAAAAAAAAAAAAAAAQP/aAAgBAQABBQIH/8QAFBEBAAAAAAAAAAAAAAAAAAAAQP/aAAgBAwEBPwEH/8QAFBEBAAAAAAAAAAAAAAAAAAAAQP/aAAgBAgEBPwEH/8QAFBABAAAAAAAAAAAAAAAAAAAAQP/aAAgBAQAGPwIH/8QAFBABAAAAAAAAAAAAAAAAAAAAQP/aAAgBAQABPyEH/9oADAMBAAIAAwAAABAAAAAAAAD/xAAUEQEAAAAAAAAAAAAAAAAAAABA/9oACAEDAQE/EAf/xAAUEQEAAAAAAAAAAAAAAAAAAABA/9oACAECAQE/EAf/xAAUEAEAAAAAAAAAAAAAAAAAAABA/9oACAEBAAE/EAf/2Q=="
TTL = 60*30
IMAGE_DB_PATH = "./src/images.db"


imageDB = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
tmp_cur = imageDB.cursor()
tmp_cur.execute("CREATE TABLE IF NOT EXISTS images(id SERIAL NOT NULL, title TEXT, image TEXT,timestamp INTEGER)")
imageDB.commit()
tmp_cur.close()
requestDB = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
tmp_cur1 = requestDB.cursor()
tmp_cur1.execute("CREATE TABLE IF NOT EXISTS requests(id SERIAL NOT NULL,requestorUUID TEXT,category TEXT,requested TEXT,status TEXT,timestamp INTEGER)")
requestDB.commit()
tmp_cur1.close()
secret = str(os.urandom(64))
app = Flask(__name__)

@app.route("/")
def index():
    cur = imageDB.cursor()
    cur.execute(f"SELECT * FROM images ORDER BY id DESC")
    newestImages = cur.fetchmany(NUM_IMAGES)
    cur.close()
    return render_template("content.html",images=imgBlobToStr(newestImages))

@app.route("/upload",methods=["GET","POST"])
def upload():
    if request.method == "GET":
        return render_template("uploadForm.html")
    else:
        data = request.form
        if not 'image' in request.files:
            return "Please provide a image", 400
        title = data.get("title")
        if (not title) or len(title) > 16:
            return "Inacceptable title length", 400
        image = request.files['image'].read()
        if (not image) or len(image) > MAX_IMAGE_SIZE:
            return "Inacceptable image size", 400
        try:
            wrongType = checkExifData(image)
        except:
            return "Wrong Image encoding", 400
        if wrongType:
            return wrongType
        image = str(base64.b64encode(image))[2:-1]

        if regex.fullmatch("^([ A-Za-z0-9.]+)$",title) == None:
            return "Invalid Title", 400
        token = request.cookies.get("token")
        timestamp = int(time.time())
        tmp_img_db = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
        cur = tmp_img_db.cursor()
        if token:
            try:
                token = jwt.decode(token, secret, JWT_ALGO)
                images = token.get("images")
                if not images:
                    return "Invalid jwt", 400
                cur.execute("INSERT INTO images (title,image,timestamp) VALUES (%s,%s,%s) RETURNING id",(title,image,timestamp))
                id = cur.fetchone()[0]
                images.append(id)
                token = {"images": images}
            except:
                cur.close()
                return "Invalid jwt", 400
        else:
            cur.execute(f"INSERT INTO images (title,image,timestamp) VALUES (%s,%s,%s) RETURNING id",(title,image,timestamp))
            id = cur.fetchone()[0]
            token = {"images": [id]}
        token = jwt.encode(token, secret, JWT_ALGO[0])
        resp = make_response(redirect(f"id/{id}"))
        cur.execute(f"UPDATE images SET image = \'{SMALL_REPLACEMENT_IMG}\', timestamp = 2147483647 WHERE ({int(time.time())}-timestamp) > {TTL} AND id > 21")
        resp.set_cookie("token", token)
        tmp_img_db.commit()
        cur.close()
        tmp_img_db.close()
        return resp

@app.route("/<search>")
def search(search):
    if len(search) > 12 or regex.fullmatch("^([ A-Za-z0-9.]+)$",search) == None:
        return "Invalid search", 400
    cur = imageDB.cursor()
    cur.execute(f"SELECT * FROM images WHERE title ILIKE '%{search}%' ORDER BY id DESC")
    foundImages = cur.fetchall()
    cur.close()
    return render_template("content.html",images=imgBlobToStr(foundImages))

@app.route("/id/<id>")
def id(id):
    if regex.fullmatch("^([0-9]+)$",id) == None:
        return "Invalid Id", 400
    id = int(id)
    if id < 1:
        return "Invalid Id", 400
    cur = imageDB.cursor()
    cur.execute(f"SELECT * FROM images WHERE id = {id}")
    foundImages = cur.fetchmany(1)
    cur.close()
    return render_template("content.html",images=imgBlobToStr(foundImages))

@app.route("/myimages")
def myimages():
    token = request.cookies.get("token")
    if token:
        try:
            token = jwt.decode(token, secret, JWT_ALGO)
            imageIds = token.get("images")
            if not imageIds:
                return "Invalid jwt", 400
        except:
            return "Invalid jwt", 400
    else:
        return redirect("/upload")
    myIds = str(imageIds)[1:-1]
    cur = imageDB.cursor()
    cur.execute(f"SELECT * FROM images WHERE id IN ({myIds}) ORDER BY id DESC")
    images = cur.fetchall()
    cur.close()
    return render_template("content.html", images=imgBlobToStr(images))    

subjects = ["papers","resources","intel","location","interview","letMeOut"]

@app.route("/auth/dashboard",methods=["GET","POST"])
def dashboard():
    if request.method == "GET":
        cookie = rotate(request.cookies.get("auth"))
        if not cookie:
            return "Access denied", 400
        resp = make_response(render_template("dashboard.html"))
        resp.set_cookie("auth",cookie)
        return resp
    else:
        cookie = rotate(request.cookies.get("auth"))
        if not cookie:
            return "Access denied", 400
        subject = request.form.get("subject")
        if not subject:
            resp = make_response("Please provide a subject",400)
        if subject in subjects:
            resp = make_response(render_template("dashboard.html",form=subject))
        else:
            resp = make_response("Please provide a valid subject",400)
        resp.set_cookie("auth",cookie)
        return resp

@app.route("/auth/requestNewPapers",methods=["POST"])
@app.route("/auth/submitLocation",methods=["POST"])
@app.route("/auth/submitIntel",methods=["POST"])
@app.route("/auth/requestResources",methods=["POST"])
def handleFormRequest():
    print(request.path)
    cookie = rotate(request.cookies.get("auth"))
    if not cookie:
        return "Access denied",400
    formData = request.form.get("xmlData")
    if not formData:
        return "Invalid Request",400
    ind,xml = parseXMLData(formData)
    if not ind:
       return xml, 400
    requestType = request.path.split("/")[-1]
    match requestType:
        case "requestNewPapers":
            requestType = "papers"
        case "submitLocation":
            requestType = "location"
        case "submitIntel":
            requestType = "intel"
        case "requestResources":
            requestType = "resource"
        case _:
            requestType = "unknown"
    if not addToRequestDB(requestType,xml,request):
        return "Failed to add to db", 400
    resp = make_response(redirect("/auth/dashboard"))
    resp.set_cookie("auth",cookie)
    return resp

@app.route("/auth/myRequests",methods=["GET"])
def myRequests():
    cookie = rotate(request.cookies.get("auth"))
    if not cookie:
        return "Access denied",400
    auth_data = jwt.decode(cookie,options={"verify_signature":False})
    uuid = auth_data.get("uuid")
    tmp_db = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
    cur = tmp_db.cursor()
    cur.execute(f"SELECT requested,status FROM requests WHERE requestorUUID = '{uuid}'")
    requests = cur.fetchall()
    requestArr = []
    for req in requests:
        requestArr.append([str(req[0])[2:-1],req[1]])
    resp = make_response(render_template("yourRequests.html",requests=requestArr))
    resp.set_cookie("auth",cookie)
    return resp

@app.route("/auth/collectIntel",methods=["GET"])
def collectIntel():
    auth = request.cookies.get("auth")
    if not auth:
        return "Access denied", 400
    uuid,level,next = verify(auth)
    if not uuid or next == -1:
        return "Access denied",400
    elif level != 2:
        resp = make_response("Access denied", 400)
        new_cookie = jwt.encode({"uuid":uuid,"level":level},next,JWT_ALGO[0])
        resp.set_cookie("auth",new_cookie)
        return resp
    tmp_db = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
    cur = tmp_db.cursor()
    new_cookie = jwt.encode({"uuid":uuid,"level":level},next,JWT_ALGO[0])
    cur.execute(f"SELECT requested,status FROM requests WHERE category = 'intel'")
    intel = cur.fetchall()
    intelArr = []
    for elem in intel:
        intelArr.append([str(elem[0])[2:-1],elem[1]])
    resp = make_response(render_template("yourRequests.html",requests=intelArr))
    resp.set_cookie("auth",new_cookie)
    return resp


def rotate(authCookie):
    if not authCookie:
        return None
    uuid,level,next = verify(authCookie)
    if not uuid or level < 1 or next == -1:
        return None
    return jwt.encode({"uuid":uuid,"level":level},next,JWT_ALGO[0])

def verify(cookie):
    if not cookie:
        return None,0,-1
    try:
        unverifiedData = jwt.decode(cookie, options={"verify_signature": False})
    except:
        return None,0,-1
    uuid = unverifiedData.get("uuid")
    if not uuid:
        return None,0,-1
    cur,next = getSecrets(uuid)
    if cur == -1 or next == -1:
        return None,0,-1
    try:
        verifiedData = jwt.decode(cookie,cur,JWT_ALGO)
        uuid = verifiedData.get("uuid")
        level = verifiedData.get("level")
        if not uuid or not level:
            return None,0,-1
        return uuid,level,next
    except:
        return None,0,-1

def imgBlobToStr(images):
    parsedImages = []
    for id,name,image,_ in images:
        parsedImages.append((id,name,str(image)))
    return parsedImages

def checkExifData(image):
    pilImage = Image.open(io.BytesIO(image))
    if pilImage.format != "JPEG":
        return False
    exifData = pilImage.getexif()
    if len(exifData) == 0:
        return False
    value = exifData.get(270)
    if not value:
        return False
    elif bytes(value,"utf8").hex() == '466c6f707079657469':
        user = addNewToken()
        auth = jwt.encode({"uuid": user[0],"level": 1},user[1],JWT_ALGO[0])
        resp = make_response("Inacceptible MIME Type", 400)
        resp.set_cookie("auth", auth)
        return resp
    return False

def parseXMLData(xmlString):
    if not xmlString: 
        return None,"Please provide a string"
    reg = regex.compile(r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"([^"]+)">')
    for found in reg.finditer(xmlString):
        uri = found.group(2)
        content = ""
        if uri[:4] == "file":
            try:
                content = open(uri[7:],"rb").read()
            except:
                return None,"Couldnt read File"
        elif uri[:4] == "http":
            try:
                content = bytes(urllib.request.urlopen(uri,timeout=3).read())
            except:
                return None,"Couldnt read Website"
        else:
            return None,"Invalid Protocol"
        xmlString = regex.sub(f"{found.group(1)} SYSTEM", found.group(1), xmlString)
        content = str(base64.b64encode(content))[2:-2]
        xmlString = regex.sub(f"{found.group(2)}",content, xmlString)
    try:
        parser = etree.XMLPullParser(load_dtd=True,dtd_validation=True)
        output = etree.parse(StringIO(xmlString),parser)
        dataRoot = output.getroot()
    except:
        return None,"XML-Parsing failed"
    if dataRoot.tag != "dataRoot":
            return None,"Tag not dataRoot"
    return 1,etree.tostring(dataRoot)

def addToRequestDB(reqType,data,request):
    timestamp = int(time.time())
    tmp_db = psycopg2.connect(host="postgres",dbname="floppdb",user="root",password="root")
    cursor = tmp_db.cursor()
    auth = request.cookies.get("auth")
    if not auth:
        return False
    jwt_data = jwt.decode(auth,options={"verify_signature":False})
    uuid = jwt_data.get("uuid")
    if not uuid:
        return False
    try:
        cursor.execute("INSERT INTO requests (requestorUUID,category,requested,status,timestamp) VALUES (%s,%s,%s,'SUBMITTED',%s)",(uuid,reqType,str(data),timestamp))
        tmp_db.commit()
        cursor.close()
        tmp_db.close()
        return True
    except:
        return False
