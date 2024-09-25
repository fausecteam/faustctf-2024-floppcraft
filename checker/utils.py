from PIL import Image,ImageDraw
from random import choice, randint
import io
import requests
import base64
import jwt
from wonderwords import RandomWord
import os
import string
import logging

JWT_ALGO = ["HS256"]
countries = ["Astrania","Azerfloppaijan","Baja California Republic","Belaflop","Bellvin","Birmanistan","Bingium","Bingustan","Bingustralia","Bingypt","Binraq","Binland","Bulgolia","Cheggola","Chiflopese Western Republic","Chiflopen republic","Ethifloppian EmpireFlopvaal/South African Republic","Fleden","Flopovo","Flobania","Flobya","Flomak Republic","Flopain","Flopan","Flopaz and Flopejd","Flopce","Flopinisa","Flopitaly","Flopkey","Flopmany","Flopmark","Flopnei Darussalam","Flopombia","Floppaflopvakia","Floppania","Floppany","Floppaslavia","Floppersian Empire","Flopgary","Floprea","Sovereign Nation of Flopsium","Flopshan Empire","Flopsrael","Flopxico","Flopystan","Floppas Land of Omelettes, Pizza, Peaches, and Apples","Flusynia","Fogslavia","Foogenzuela","Geofrikaan Republik","Gloptica","Democratic Republic of the Bongo","Googalia","Googas Fort","Gloopistan","Goomistan","Great Sogtain","Herbertia","Indochiflop","Indofloppia","Islaflopia","Northern Fyprus","Republic of Chiflop","Republic Of Freece","Saudi Flopparia","Republic of Soggi","Republic of Southern Soggi","Republic of Zabloing","Sogada","Sogden","Soggastan","Soggeria","Soggerland","Soggia","Sogland","Soggmania","Sogstria","United States of Sogalaysia","The Flopperlands","United Flops of America","Yucatan Republic"]
def generateRandomImage():
    rand = randint(0,5)
    if rand < 3:
        width = randint(1,300)
        height = randint(1,300)
        image = Image.new("RGB",(width,height),"white")
        draw = ImageDraw.Draw(image)
        pixel = randint(0,width*height)
        for _ in range(pixel):
            x = randint(0,width-1)
            y = randint(0,width-1)
            color = (randint(0,255),randint(0,255),randint(0,255))
            draw.point((x,y),fill=color)
        imgByteArr = io.BytesIO()
        image.save(imgByteArr,format="jpeg")
        return Image.open(imgByteArr)
    else:
        files = os.listdir(os.path.dirname(os.path.realpath(__file__))+"/images/")
        return Image.open(os.path.dirname(os.path.realpath(__file__))+"/images/"+files[randint(0,len(files)-1)])

def genRandomTitle(length,addInvalid):
    r = RandomWord()
    try:
        word = r.random_words(include_parts_of_speech=["nouns", "adjectives","verbs"],word_min_length=length,word_max_length=length,regex="^([ A-Za-z0-9.]+)$")[0]
    except:
        word = length*chr(randint(97,122))
    if not addInvalid:
        return word
    if length > 1:
        index = randint(0,length-1)
    else:
        index = 0
    invalid = ["\"","!","=","?","ß","&","§","-","_","+","~","*","'","#",">","<","|","@","ä","ö","ü","µ"]
    invalid_index = randint(0,len(invalid)-1)
    word = list(word)
    word[index] = invalid[invalid_index]
    word = str(word)
    return word

def addFloppyeti(image):
    exifdata = image.getexif()
    exifdata[270] = "Floppyeti"
    imgByteArr = io.BytesIO()
    image.save(imgByteArr,format="jpeg",exif=exifdata)
    return Image.open(imgByteArr)

def fromPILImageToBytes(image):
    imageByteArray = io.BytesIO()
    image.save(imageByteArray,format="JPEG",exif=image.getexif())
    return imageByteArray.getvalue()

def fromBytesToPILImage(imageBytes):
    return Image.open(io.BytesIO(imageBytes))

def uploadImage(self,s,title,imageAsBytes):
    if s:
        return s.post(f"http://[{self.ip}]:5000"+"/upload",data={"title":title},files={"image":imageAsBytes})
    return requests.post(f"http://[{self.ip}]:5000"+"/upload",data={"title":title},files={"image":imageAsBytes})    

def isImageOnSite(siteText,base64EncodedImage):
    imagesStr = str(base64EncodedImage)[2:-1]
    images = siteText.find(imagesStr)
    if images:
        return True
    return False

def requestCategorie(self,categorie):
    return requests.get(f"http://[{self.ip}]:5000"+"/"+categorie)

def requestId(self,s,id):
    if s:
        return s.get(f"http://[{self.ip}]:5000"+"/id/"+id)
    return requests.get(f"http://[{self.ip}]:5000"+"/id/"+id)

def requestOwnPictures(self,s):
    if s:
        return s.get(f"http://[{self.ip}]:5000"+"/myimages")
    return requests.get(f"http://[{self.ip}]:5000"+"/myimages")

def getIdsFromJWT(cookies):
    if cookies == None:
        logging.error("getIdsFromJWT: no cookies")
        return None
    jwt_token = cookies.get("token")
    if not jwt_token:
        logging.error("getIdsFromJWT: no token in cookies")
        return None
    try:
        jwt_data = jwt.decode(jwt_token,options={"verify_signature": False})
    except:
        logging.exception("Failed to decode JWT (getIdsFromJWT)")
        return None
    return jwt_data.get("images")

def uploadNImages(self,session,num,idArray):
    if not session:
        session = requests.session()
    count = 0
    for _ in range(num):
        resp = uploadImage(self,session,genRandomTitle(randint(1,16),False),fromPILImageToBytes(generateRandomImage()))
        if resp.status_code != 200:
            continue
        count += 1
        idArray.append(int(resp.url.split("/")[-1]))
    return count

def buildRequestVisual(requestType,dataArray):
    if requestType == "intel":
        return f"<dataRoot><formType>intel</formType><intel>{dataArray[0]}</intel><topsecret>{dataArray[1]}</topsecret></dataRoot>"
    elif requestType == "papers":
        return f"<dataRoot><formType>papers</formType><birthcountry>{dataArray[0]}</birthcountry><citizenship>{dataArray[1]}</citizenship><fname>{dataArray[2]}</fname><lname>{dataArray[3]}</lname><papers-attributes>{dataArray[4]}</papers-attributes><day>{dataArray[5]}</day><month>{dataArray[6]}</month><year>{dataArray[7]}</year></dataRoot>"
    elif requestType == "location":
        return f"<dataRoot><formType>location</formType><latitude>{dataArray[0]}</latitude><longitude>{dataArray[1]}</longitude><description>{dataArray[2]}</description></dataRoot>"
    elif requestType == "resources":
        return f"<dataRoot><formType>resources</formType><description>{dataArray[0]}</description><amount>{dataArray[1]}</amount><reason>{dataArray[2]}</reason></dataRoot>"

# Actual Checks

# Check Title Length Behaviour
def checkTitleLength(self,session,length):
    print("[Check Title Length in upload]")
    if not session:
        session = requests.session()
    if length == -1:
        length = randint(0,22)
    title = genRandomTitle(length,False)
    image = fromPILImageToBytes(generateRandomImage())
    base64Image = base64.b64encode(image)    
    resp = uploadImage(self,session,title,image)
    if length > 0 and length <= 16:
        try:
            id = int(resp.url.split("/")[-1])
        except:
            print(title)
            print(base64Image)
            print(resp.status_code)
            print(resp.history)
            return False
        jwtIds = getIdsFromJWT(session.cookies)
        if resp.status_code == 200 and isImageOnSite(resp.text,base64Image) and session.cookies.get("token") and jwtIds and (id in jwtIds):
            return True
        else:
            return False
    else:
        if resp.status_code == 400:
            return True
        else:
            return False

# Check if Title can have invalid Characters
def checkInvalidCharacters(self):
    print("[Check invalid characters in upload]")
    session = requests.session()
    title = genRandomTitle(randint(1,16),True)
    image = fromPILImageToBytes(generateRandomImage())
    resp = uploadImage(self,session,title,image)
    if not session.cookies.get("token") and resp.status_code == 400:
        return True
    return False

def checkByteEncoding(self):
    print("[Check byte encoding in upload]")
    session = requests.session()
    title = genRandomTitle(randint(1,16),False)
    image = generateRandomImage().tobytes()
    resp = uploadImage(self,session,title,image)
    if resp.status_code == 400 and not session.cookies.get("token"):
        return True
    print(resp.status_code)
    return False

def checkForNImages(session,num):
    print("[Check uploading multible images]")
    if not session:
        raise Exception("Please provide a session!")
    ids = getIdsFromJWT(session.cookies)
    logging.info(f"checkForNImages: got {len(ids)} images, wanted {num}")
    if ids:
        if len(ids) == num:
            return True
    return False

def checkForSameIdsInJWT(session,idArray):
    print("[Checking if uploaded same in JWT]")
    return getIdsFromJWT(session.cookies) == idArray

def checkInvalidJWTUpload(self,session):
    print("[Check invalid JWT upload]")
    jwt_enc = session.cookies.get("token")
    if not jwt:
        raise Exception("Please upload images first!")
    try:    
        jwt_data = jwt.decode(jwt_enc,options={"verify_signature": False})
    except:
        logging.exception("checkInvalidJWTUpload: Failed to decode jwt")
        return False
    jwt_enc_evil = jwt.encode(jwt_data,"ultimateSecret",JWT_ALGO[0])
    new_session = requests.Session()
    new_session.cookies.set("token",jwt_enc_evil)
    resp = uploadImage(self,new_session,genRandomTitle(randint(1,16),False),fromPILImageToBytes(generateRandomImage()))
    if resp.status_code != 400:
        return False
    return True

def checkBehavoirOfGetInSecret(self,session):
    print("[Check behaviour of auth]")
    resp = session.get(f"http://[{self.ip}]:5000"+"/auth/"+choice(["dashboard","myRequests"]))
    if resp.status_code == 200:
        return True
    return False

def checkInvalidJWTSecret(self,session):
    print("[Check invalid JWT in auth]")
    jwt_enc = session.cookies.get("auth")
    if not jwt_enc:
        raise Exception("You dont have a auth Token")
    try:
        jwt_data = jwt.decode(jwt_enc,options={"verify_signature": False})
    except:
        logging.exception("checkInvalidJWTSecret exception")
        return False
    jwt_enc_evil = jwt.encode(jwt_data,"ultimateSecret",JWT_ALGO[0])
    new_session = requests.Session()
    new_session.cookies.set("auth",jwt_enc_evil)
    resp = new_session.get(f"http://[{self.ip}]:5000"+"/auth/dashboard")
    if resp.status_code != 400:
        return False
    return True

def checkIfSecretImageWorks(self,session,image):
    print("[Check if secret image works]")
    try:
        if session == None:
            session = requests.session()
        if image == None:
            image = generateRandomImage()
        image = fromPILImageToBytes(addFloppyeti(image))
        resp = uploadImage(self,session,genRandomTitle(randint(1,15),False),image)
        if resp.status_code != 400:
            print("No 400")
            return False
        auth = session.cookies.get("auth")
        if not auth:
            print("Cant find auth")
            return False
        jwt_data = jwt.decode(auth,options={"verify_signature": False})
        if not jwt_data.get("level") or not jwt_data.get("uuid"):
            print("Cant find in jwt")
            return False
        return True
    except:
        logging.exception("checkIfSecretImageWorks exception")
        return True

def checkIfIntelSubmitWorks(self,session,intel,topsecret):
    print("[Check if intel submission works]")
    resp = session.post(f"http://[{self.ip}]:5000/auth/submitIntel",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/intel.dtd\"><dataRoot><formType>intel</formType><intel>{intel}</intel><topsecret>{str(topsecret)}</topsecret></dataRoot>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})
    if resp.status_code >= 400:
        return False
    return True

def checkIfLocationSubmitWorks(self,session,longtitude,latitude,description):
    print("[Check if location submission works]")
    resp = session.post(f"http://[{self.ip}]:5000/auth/submitLocation",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/location.dtd\"><dataRoot><formType>location</formType><latitude>{latitude}</latitude><longitude>{longtitude}</longitude><description>{description}</description></dataRoot>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})
    if resp.status_code >= 400:
        return False
    return True

def checkIfPaperSubmitWorks(self,session,birthcountry,citizenship,fname,lname,silly,day,month,year):
    print("[Check if paper submission works]")
    resp = session.post(f"http://[{self.ip}]:5000/auth/requestNewPapers",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/papers.dtd\"><dataRoot><formType>papers</formType><birthcountry>{birthcountry}</birthcountry><citizenship>{citizenship}</citizenship><fname>{fname}</fname><lname>{lname}</lname><papers-attributes>{silly}</papers-attributes><day>{day}</day><month>{month}</month><year>{year}</year></dataRoot>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})
    if resp.status_code >= 400:
        return False
    return True

def checkIfResourceSubmitWorks(self,session,description,amount,reason):
    print("[Check if resource submission works]")
    resp = session.post(f"http://[{self.ip}]:5000/auth/requestResources",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/resources.dtd\"><dataRoot><formType>resources</formType><description>{description}</description><amount>{amount}</amount><reason>{reason}</reason></dataRoot>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})
    if resp.status_code >= 400:
        return False
    return True
    
def checkCollectIntel(self,session):
    print("[Check if collect Intel works]")
    resp = session.get(f"http://[{self.ip}]:5000/auth/collectIntel")
    if resp.status_code != 400:
        return False
    resp = session.get(f"http://[{self.ip}]:5000/auth/dashboard")
    if resp.status_code != 200:
        return False
    return True

def checkIfInvalidRequestWorks(self,session):
    print("[Check invalid requests]")
    num = randint(1,4)
    rw = genRandomTitle(randint(3,9),False)
    resp = None
    match num:
        case 1:
            resp = session.post(f"http://[{self.ip}]:5000/auth/submitIntel",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/intel.dtd\"><{rw}><formType>intel</formType><intel>{genRandomTitle(randint(1,11),False)}</intel><topsecret>{str(choice([True,False]))}</topsecret></{rw}>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})
        case 2:
            resp = session.post(f"http://[{self.ip}]:5000/auth/submitLocation",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/location.dtd\"><{rw}><formType>location</formType><latitude>{str(randint(-89,89))+'.'+str(randint(0,999999))}</latitude><longitude>{str(randint(-179,179))+'.'+str(randint(0,999999))}</longitude><description>{choice(string.ascii_letters) * randint(1,8)}</description></{rw}>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})
        case 3:
            resp = session.post(f"http://[{self.ip}]:5000/auth/requestNewPapers",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/papers.dtd\"><{rw}><formType>papers</formType><birthcountry>{choice(countries)}</birthcountry><citizenship>{choice(countries)}</citizenship><fname>{choice(string.ascii_letters) * randint(1,9)}</fname><lname>{choice(string.ascii_letters) * randint(1,7)}</lname><papers-attributes>{str(choice([True,False]))}</papers-attributes><day>{randint(0,31)}</day><month>{randint(0,12)}</month><year>{randint(0,4000)}</year></{rw}>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})
        case 4:
            resp = session.post(f"http://[{self.ip}]:5000/auth/requestResources",data=f"xmlData=<!DOCTYPE+dataRoot+SYSTEM+\"/src/static/resources.dtd\"><{rw}><formType>resources</formType><description>{choice(string.ascii_letters) * randint(1,8)}</description><amount>{str(randint(0,9))}</amount><reason>{choice(string.ascii_letters) * randint(3,7)}</reason></{rw}>",headers= {'Content-Type': 'application/x-www-form-urlencoded'})    
    if not resp:
        return True
    if resp.status_code != 400:
        return False
    return True
