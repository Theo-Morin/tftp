"""
TFTP Module.
"""

########################################################################
#                               Authors                                #
#                  Théo Morin : contact@theomorin.fr                   #
#           Théo Berthier : theo.berthier@etu.u-bordeaux.fr            #
########################################################################


import socket
import sys



########################################################################
#                          COMMON ROUTINES                             #
########################################################################

def printLog(s, c, data, order):
    opcode, count, _, _ = decode(data)
    req = ""
    if opcode == 1: req = "RRQ"
    elif opcode == 2: req = "WRQ"
    elif opcode == 3: req = "DAT" + str(count)
    elif opcode == 4: req = "ACK" + str(count)
    if order == 1:
        print("\033[96m["+str(s[0])+":"+str(s[1])+" -> "+str(c[0])+":"+str(c[1])+"] "+req+"="+str(data))
    else:
        print("\033[94m["+str(c[0])+":"+str(c[1])+" -> "+str(s[0])+":"+str(s[1])+"] "+req+"="+str(data))

########################################################################


def createACK(count):
    return b'\x00\x04' + count.to_bytes(2, 'big')

########################################################################


def createDAT(count, data):
    return b'\x00\x03' + count.to_bytes(2, 'big') + bytearray(data, 'utf-8')

########################################################################


def truncateFile(filename):
    open(filename, 'w').close()

########################################################################


def writeInFile(filename,data):
    try:
        file = open(filename, "w")
        for contenu in data:
            file.write(contenu)
        file.close()
    except Exception as e:
        print("\033[91mProblème d'ecriture dans le fichier :",filename)

########################################################################


def addToFile(filename,data):
    try:
        # file = open(filename, "w")
        # for contenu in data:
        #     file.write(contenu)
        # file.close()
        file = open(filename, "a")
        file.write(data)
        file.close()
    except Exception as e:
        print("\033[91mProblème d'ecriture dans le fichier :",filename)

########################################################################


# code vérifé le contenue du fichier coté serveur s'envoie par paquet de taille blksize
def fileTreatment(sc,addr,filename,blksize,cmd):
    try:
        count = 1
        with open(filename,'r') as file:
            data = ""
            while len(data) == blksize or count == 1:
                data = file.read(blksize)
                try:
                    addrc = sc.getsockname()
                    if count > 1 or cmd =="WRQ":
                        receiveddata,addrm = sc.recvfrom(1024)
                        opcode , num, _, _ = decode(receiveddata)
                        if cmd == "WRQ":
                            pass
                            printLog(addr, addrc, receiveddata, 1)
                        else:
                            print('\033[0m[{}:{}] client request: {}'.format(addrm[0], addrm[1], receiveddata))
                    else:
                        num = (count-1)
                        opcode = 4
                    if opcode == 4 and num == (count-1):
                        DAT = createDAT(count, data)
                        sc.sendto(DAT, addr)
                        if cmd == "WRQ":
                            printLog(addr, addrc, DAT, 2)
                        count = count + 1
                except:
                    print("\033[91mImpossible d'envoyer le packet au client.")
                    return False
        return True
    except Exception as e:
        print("\033[91mImpossible de lire dans le fichier.\n")
        return False

########################################################################


def decode(data):
    frame = data                                            # sample of WRQ as byte array
    frame1 = frame[0:2]                                     # Contient l'OP Code
    frame2 = frame[2:]                                      # frame2 = b'test.txt\x00octet\x00'
    opcode = int.from_bytes(frame1, byteorder='big')        # opcode = 2
    if opcode == 1 or opcode == 2:
        args = frame2.split(b'\x00')                        # args = [b'test.txt', b'octet', b'']
        filename = args[0].decode('ascii')                  # filename = 'test.txt'
        mode = args[1].decode('ascii')                      # mode = 'octet'
        blksize = args[3].decode('ascii')
        return [opcode, filename, mode, int(blksize)]
    elif opcode == 3:
        # todo : b'\x00\x02BBBBBBBBBB'
        num = int.from_bytes(frame2[0:2], byteorder='big')
        data = frame2[2:].decode()
        return [opcode, num, data, None]
    elif opcode == 4:
        num = int.from_bytes(frame2[0:2], byteorder='big')
        return [opcode, num, None, None]

########################################################################
#                             SERVER SIDE                              #
########################################################################

def runServer(addr, timeout, thread):
    # todo
    print("\033[93mLancement du serveur...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(addr)
        #création nouvelle socket pour recevoir/envoyer les données depuit le serveur sans passer par le port 6969
        sr = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("\033[92mServeur lancé sur le port", addr[1])
    except Exception as e:
        print("\033[91mErreur lors du lancement du serveur.")

    while True:
        data, addrm = s.recvfrom(1500)
        print('\033[0m[{}:{}] client request: {}'.format(addrm[0], addrm[1], data))
        opcode, _, _, _ = decode(data)
        if opcode == 1:
            # la fonction write coté client ecrie dans un nouveau fichier le contenu reçu
            # les ACK seront envoyer du côté client vers le serveur pour confirmer la récéption.
            opcode, filename, mode, blksize = decode(data)
            fileTreatment(sr,addrm,filename,blksize,"RRQ")
        if opcode == 2:
            opcode, filename, mode, blksize = decode(data)
            sr.sendto(createACK(0),addrm)
        if opcode == 3:
            _ , num , text , _ = decode(data)
            addToFile(filename,text)
            s.sendto(createACK(num),addrm)
            if len(text) < blksize:
                print("\033[92mL'intégralité du fichier vient d'être réceptionné !")
      
        # s.sendto(data, addrm)
        # print(data)
    s.close()
    pass

########################################################################
#                             CLIENT SIDE                              #
########################################################################

def connect(addr):
    print("\033[93mConnexion au serveur..")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("\033[92mConnexion au serveur établie.")
        return s
    except Exception as e:
        print("\033[91mErreur lors de la connexion au serveur.")
        return None
    pass

########################################################################


def put(addr, filename, targetname, blksize, timeout):
    s = connect(addr)
    req = b'\x00\x02' + bytearray(targetname, 'utf-8') + b'\x00octet\x00' + b'blksize' +b'\x00' + bytearray(str(blksize),"utf-8") +b'\x00'
    s.sendto(req, addr)
    addrc = s.getsockname()
    printLog(addr, addrc, req, 2)
    f = fileTreatment(s,addr,filename,blksize,"WRQ")
    if f:
        print("\033[92mL'intégralité du fichier vient d'être envoyé !")
    s.close()

########################################################################


def get(addr, filename, targetname, blksize, timeout):
    s = connect(addr)
    req = b'\x00\x01' + bytearray(filename, 'utf-8') + b'\x00octet\x00' + b'blksize' +b'\x00' + bytearray(str(blksize),"utf-8") +b'\x00' # Exemple : b'\x00\x01hello.txt\x00octet\x00'
    s.sendto(req, addr)
    addrc = s.getsockname()
    printLog(addr, addrc, req, 2)
    # ToDo  
    if len(targetname) == 0:
        targetname = filename
    truncateFile(targetname)
    while True:
        data, addr = s.recvfrom(1024)
        printLog(addr, addrc, data, 1)
        opcode, num, data, _ = decode(data)
        if opcode == 3:
            addToFile(targetname, data)
            req = createACK(num)
            s.sendto(req, addr)
            printLog(addr, addrc, req, 2)
            if len(data) < blksize:
                print("\033[92mL'intégralité du fichier vient d'être récupéré !")
                break
    # print('[{}:{}] server reply: {}'.format(addr[0], addr[1], data))
    s.close()
    pass
# EOF