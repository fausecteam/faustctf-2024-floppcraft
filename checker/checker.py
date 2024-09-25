#!/usr/bin/env python3

from random import randint, choice, shuffle
from ctf_gameserver import checkerlib
import requests
import utils
import html
import base64
import logging

class TemplateChecker(checkerlib.BaseChecker):

    def place_flag(self, tick):
        flag = base64.urlsafe_b64encode(checkerlib.get_flag(tick).encode())
        session = requests.session()
        try:
            if not utils.checkIfSecretImageWorks(self,session,None):
                logging.error("Secret Image failed")
                return checkerlib.CheckResult.FAULTY
            if not utils.checkIfIntelSubmitWorks(self,session,flag,choice([True,False])):
                logging.error("Intel Submit failed")
                return checkerlib.CheckResult.FAULTY
            checkerlib.store_state(f"flag{tick}Session",session)
            checkerlib.store_state(f"flag{tick}",flag)
            return checkerlib.CheckResult.OK
        except:
            return checkerlib.CheckResult.DOWN

    def check_service(self):
        # Checking first site (Image Upload)
        sequence = [1,2,3,4,5]
        for i in range(randint(0,3)):
            sequence.append(randint(1,5))
        shuffle(sequence)
        normal = True
        try:
            for i in sequence:
                if i == 1:
                    if not utils.checkTitleLength(self,None,-1):
                        logging.error("checkTitleLength failed")
                        normal = False
                        break
                elif i == 2:
                    if not utils.checkInvalidCharacters(self):
                        logging.error("checkInvalidCharacters failed")
                        normal = False
                        break
                elif i == 3:
                    if not utils.checkByteEncoding(self):
                        logging.error("checkByteEncoding failed")
                        normal = False
                        break
                elif i == 4:
                    session = requests.session()
                    idArray = []
                    num = utils.uploadNImages(self,session,randint(1,5),idArray)
                    if not utils.checkForNImages(session,num):
                        logging.error("chehkForNImages failed")
                        normal = False
                        break
                    if not utils.checkForSameIdsInJWT(session,idArray):
                        logging.error("checkForSameIdsInJWT failed")
                        normal = False
                        break
                    if not utils.checkInvalidJWTUpload(self,session):
                        logging.error("checkInvalidJWTUpload failed")
                        normal = False
                        break
                elif i == 5:
                    secretSession = requests.session()
                    if not utils.checkIfSecretImageWorks(self,secretSession,None):
                        logging.error("checkIfSecretImageWorks failed")
                        normal = False
                        break
                    if not utils.checkBehavoirOfGetInSecret(self,secretSession):
                        logging.error("checkBehaviorOfGetInSecret failed")
                        normal = False
                        break
                    if not utils.checkInvalidJWTSecret(self,secretSession):
                        logging.error("checkInvalidJWTSecret failed")
                        normal = False
                        break
        except:
            return checkerlib.CheckResult.DOWN
        if not normal:
            return checkerlib.CheckResult.FAULTY
        
        # Check auth capabilities
        print("----- Starting to check auth -----")
        sentRequests = []
        savedSession = requests.session()
        sequence = [1,2,3,4,choice([2,3])]
        shuffle(sequence)
        index2 = sequence.index(1)
        index5 = sequence.index(4)
        while index2 > index5:
            shuffle(sequence)
            index2 = sequence.index(1)
            index5 = sequence.index(4)
        validSession = requests.session()
        try:
            if not utils.checkIfSecretImageWorks(self,validSession,None):
                return checkerlib.CheckResult.FAULTY
            for i in sequence:
                if i == 1:
                    # Upload some requests
                    print("----- Uploading Requests -----")
                    for i in range(randint(2,7)):
                        num = randint(1,4)
                        if num == 1:
                            topS = str(choice([True,False]))
                            intel = utils.genRandomTitle(8,False)
                            sentRequests.append(utils.buildRequestVisual("intel",[intel,topS]))
                            try:
                                if not utils.checkIfIntelSubmitWorks(self,validSession,intel,topS):
                                    normal = False
                                    break
                            except:
                                break
                        elif num == 2:
                            latitude = str(randint(-90,90))+'.'+str(randint(0,999999))
                            longtitude = str(randint(-180,180))+'.'+str(randint(0,999999))
                            description = utils.genRandomTitle(randint(5,11),False)
                            sentRequests.append(utils.buildRequestVisual("location",[latitude,longtitude,description]))
                            try:
                                if not utils.checkIfLocationSubmitWorks(self,validSession,longtitude,latitude,description):
                                    normal = False
                                    break
                            except:
                                break
                        elif num == 3:
                            birthcountry = choice(utils.countries)
                            citizenship = choice(utils.countries)
                            fname = utils.genRandomTitle(randint(1,8),False)
                            lname = utils.genRandomTitle(randint(1,8),False)
                            pa = str(choice([True,False]))
                            day = str(randint(1,31))
                            month = str(randint(1,12))
                            year = str(randint(-13,4000))
                            sentRequests.append(utils.buildRequestVisual("papers",[birthcountry,citizenship,fname,lname,pa,day,month,year]))
                            try:
                                if not utils.checkIfPaperSubmitWorks(self,validSession,birthcountry,citizenship,fname,lname,pa,day,month,year):
                                    normal = False
                                    break
                            except:
                                break
                        elif num == 4:
                            description = utils.genRandomTitle(randint(3,9),False)
                            amount = str(randint(1,199))
                            reason = utils.genRandomTitle(randint(1,18),False)
                            sentRequests.append(utils.buildRequestVisual("resources",[description,amount,reason]))
                            try:
                                if not utils.checkIfResourceSubmitWorks(self,validSession,description,amount,reason):
                                    normal = False
                                    break
                            except:
                                break
                    savedSession = validSession
                    validSession = requests.session()
                    if not utils.checkIfSecretImageWorks(self,validSession,None):
                        normal = False
                        break
                elif i == 2:
                    print("----- Checking collectIntel -----")
                    # Check if Access Denied in /auth/collectIntel
                    if not utils.checkIfSecretImageWorks(self,validSession,None):
                        normal = False
                        break
                    if not utils.checkCollectIntel(self,validSession):
                        normal = False
                        break
                elif i == 3:
                    print("----- Check if Invalid Request works -----")
                    # Check if Invalid Request works
                    try:
                        res = utils.checkIfInvalidRequestWorks(self,validSession)
                    except:
                        return checkerlib.CheckResult.OK
                    if not res:
                        normal = False
                        break
                    if not utils.checkIfSecretImageWorks(self,validSession,None):
                        normal = False
                        break
                    break
                elif i == 4:
                    print("----- Check myRequests -----")
                    # Check myRequests
                    session = savedSession
                    resp = session.get(f"http://[{self.ip}]:5000/auth/myRequests")
                    if resp.status_code != 200:
                        print("No 200")
                        normal = False
                        break
                    for i in sentRequests:
                        if html.unescape(resp.text).find(i) == -1:
                            print(f"Cant find a request {i}")
                            print(html.unescape(resp.text))
                            normal = False
                            break
                    break
        except:
            return checkerlib.CheckResult.DOWN
        if not normal:
            return checkerlib.CheckResult.FAULTY
        return checkerlib.CheckResult.OK

    def check_flag(self, tick):
        session = checkerlib.load_state(f"flag{tick}Session")
        flag = checkerlib.load_state(f"flag{tick}")
        try:
            resp = session.get(f"http://[{self.ip}]:5000/auth/myRequests")
        except:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        checkerlib.store_state(f"flag{tick}Session",session)
        if resp.status_code != 200:
            return checkerlib.CheckResult.FAULTY
        if resp.text.find(flag.decode()) == -1:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        return checkerlib.CheckResult.OK


if __name__ == '__main__':

    checkerlib.run_check(TemplateChecker)
