from socket import *
import os
import sys
import struct
import time
import select
import binascii
from math import sqrt
from functools import reduce
ICMP_ECHO_REQUEST = 8
pingSum=0
pingMin=float("+infinity")
pingMax=0
lista=[]
def checksum(string):
    string = bytearray(string)
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = (string[count+1]) * 256 + (string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(string):
        csum = csum + (string[len(string) - 1])
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff 
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer
def receiveOnePing(mySocket, ID, timeout, destAddr):
    global pingSum,pingMin,pingMax,lista
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return -1
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        timeLeft = timeLeft - howLongInSelect
        
##################################################### Fill in start ######################################################
        try:
            icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", recPacket[20:28])
            
            send_time=struct.unpack('d',recPacket[28:])[0]

            rtt=(timeReceived-send_time)*1000
            
            pingSum+=rtt
            lista.append(rtt)
            pingMin=int(min(pingMin,rtt))
            pingMax=int(max(pingMax,rtt))
            # mostrar carimbo data/hora
            ip_header=struct.unpack('!BBHHHBBH4s4s',recPacket[:20])
            ttl=ip_header[5]
            length = len(recPacket)-20
            #Fetch the ICMP header from the IP packet
            return length,ttl,rtt
        except:
            return -1
###################################################### Fill in end ######################################################
        if timeLeft <= 0:
            return -1
        
def sendOnePing(mySocket, destAddr, ID):
        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.
def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.
def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type. For more details: http://sockraw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    myID = os.getpid() & 0xFFFF # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay
def desvio(lista):
    mean = sum(lista) / len(lista)
    return sqrt(reduce(lambda x, y: x + y, map(lambda x: (x - mean) ** 2, lista)) / len(lista))
def ping(ciclos,host, timeout=1):
    global pingSum,pingMin,pingMax,lista
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    pingSum=0
    pingMin=float("+infinity")
    pingMax=0
    pingCnt=0
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Send ping requests to a server separated by approximately one second
    delay = doOnePing(dest, timeout)
    if delay==-1:
        print(f'Resposta de {dest}: Host de destino inacessível.')
    else:
        pingCnt+=1
        print(f"Disparado {dest} com {delay[0]} bytes de dados")
        print(f'Resposta de {dest}: bytes={delay[0]} tempo={int(delay[2])}ms TTL={delay[1]}')
    for i in range(ciclos-1):
        delay = doOnePing(dest, timeout)
        if delay==-1:
            print(f'Resposta de {dest}: Host de destino inacessível.')
        else:
            pingCnt+=1
            print(f'Resposta de {dest}: bytes={delay[0]} tempo={int(delay[2])}ms TTL={delay[1]}') 
        time.sleep(1)# one second
    print(f'Estatísticas do Ping para {dest}:')
    print(f'\tPacotes: Enviados={ciclos}, recebidos={pingCnt}, Perdidos={ciclos-pingCnt} ({100*(ciclos-pingCnt)/ciclos}% de perda)')
    print('Aproximar um número redondo de vezes em milissegundos:')
    print(f'\tMínimo={pingMin}ms, Máximo={pingMax}ms, Média={0 if pingCnt==0  else int(pingSum/pingCnt)}ms, Desvio Padrão={int(desvio(lista))}ms')

    return delay
print('################ Oceania ##################')
ping(4,"sydney.edu.au")
print("################ America do norte ########")
ping(4,"harvard.edu")
print('################ Asia ####################')
ping(4,"uec.ac.jp")
print('################ Europa ##################')
ping(4,"uc.pt")