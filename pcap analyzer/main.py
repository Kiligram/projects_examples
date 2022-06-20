# Python 3.9 / PyCharm
# Andrii Rybak
import os.path
import scapy.all as scapy


def printHexPcap(frame):
    for j in range(len(frame)):
        if j != 0 and (j % 2) == 0:
            print(" ", end="")
            if (j % 16) == 0:
                print(" ", end="")
                if (j % 32) == 0: print("")
        print(frame[j], end="")
    print("")


def printMac(frame):
    i = 12
    print("Zdrojova MAC adresa: ", end="")
    while i < 24:
        if i != 12 and i % 2 == 0:
            print(" ", end="")
        print(frame[i], end="")
        i += 1
    print("")

    print("Cielova MAC adresa: ", end="")
    i = 0
    while i < 12:
        if i != 0 and i % 2 == 0:
            print(" ", end="")
        print(frame[i], end="")
        i += 1
    print("")


def printLength(frame):
    length = int(len(frame) / 2)
    print("dĺžka rámca poskytnutá pcap API – " + str(length) + " B")
    print("dĺžka rámca prenášaného po médiu – " + str(length + 4 if length >= 60 else 64) + " B")


def printFrameType(frame):
    typeInt = int(frame[24:28],  16)
    if typeInt >= 1536:
        print("Ethernet II")
        return "ether2"
    elif typeInt <= 1500 and frame[28:32] == "ffff":
        print("IEEE 802.3 – Raw")
        return "raw"
    elif typeInt <= 1500 and frame[28:32] == "aaaa":
        print("IEEE 802.3 s LLC a SNAP")
        return "snap"
    elif typeInt <= 1500:
        print("IEEE 802.3 LLC")
        return "llc"


def insertProtsInList(protFile, j, protTypeList):
    while protFile[j] != "--":
        j += 1
        if protFile[j] == "--": break
        temp = protFile[j].split(" ", 1)
    #    print(temp)
        protTypeList[int(temp[0], 16)] = temp[1]

    return j


def printNestedProt(frameType, frameInHex):
    if frameType == "raw": print("IPX")
    elif frameType == "ether2":
        if etherTypes[int(frameInHex[24:28], 16)] is None:
            print(f"Unknown protocol 0x{frameInHex[24:28]}")
        else:
            print(etherTypes[int(frameInHex[24:28], 16)])

    elif frameType == "llc":
        if lsaps[int(frameInHex[28:30], 16)] is None:
            print(f"Unknown protocol 0x{frameInHex[28:30]}")
        else:
            print(lsaps[int(frameInHex[28:30], 16)])

    elif frameType == "snap":
        if etherTypes[int(frameInHex[40:44], 16)] is None:
            print(f"Unknown protocol 0x{frameInHex[40:44]}")
        else:
            print(etherTypes[int(frameInHex[40:44], 16)])


def formatIp(string):
    return (f"{int(string[0:2], 16)}."
            f"{int(string[2:4], 16)}."
            f"{int(string[4:6], 16)}."
            f"{int(string[6:8], 16)}")


def tcp(frameInHex):
    sPort = int(frameInHex[:4], 16)
    dPort = int(frameInHex[4:8], 16)
    if tcpPorts[min(sPort, dPort)] is None:
        print(f"Unknown port")
    else:
        print(tcpPorts[min(sPort, dPort)])

    print(f"zdrojový port: {sPort}")
    print(f"cieľový port: {dPort}")


def udp(frameInHex, frame, pcap, frameNum):
    sPort = int(frameInHex[:4], 16)
    dPort = int(frameInHex[4:8], 16)

    sPortHex = frameInHex[:4]
    dPortHex = frameInHex[4:8]

    if dPortHex == "0045":
        tftpPort = findNextTFTPport(pcap, frameNum, frame[24:32], sPortHex, frame[32:40])
        TFTPportsList.append([frame[32:40], tftpPort])

    if udpPorts[min(sPort, dPort)] is None:
        flag = False
        for i in TFTPportsList:
            if (i[0] == frame[24:32] and i[1] == sPortHex) or (i[0] == frame[32:40] and i[1] == dPortHex):
                print("TFTP")
                flag = True
                break
        if not flag:
            print(f"Unknown port")
    else:
        print(udpPorts[min(sPort, dPort)])

    print(f"zdrojový port: {sPort}")
    print(f"cieľový port: {dPort}")


def icmp(frameInHex):
    if icmpTypes[int(frameInHex[0:2], 16)] is None:
        print(f"Unknown ICMP type 0x{frameInHex[0:2]}")
    else:
        print(icmpTypes[int(frameInHex[0:2], 16)])


def ipv4(frameInHex, ipv4Stats, pcap, frameNum):
    print(f"zdrojová IP adresa: {formatIp(frameInHex[24:32])}")
    print(f"cieľová IP adresa: {formatIp(frameInHex[32:40])}")

    if ipProts[int(frameInHex[18:20], 16)] is None:
        print(f"Unknown protocol 0x{frameInHex[18:20]}")
    else:
        print(ipProts[int(frameInHex[18:20], 16)])

    if ipv4Stats is not None:
        if not frameInHex[24:32] in ipv4Stats:
            ipv4Stats.append(frameInHex[24:32])
            ipv4Stats.append(1)
        else:
            ipv4Stats[ipv4Stats.index(frameInHex[24:32]) + 1] += 1

    if frameInHex[18:20] == "06":
        tcp(frameInHex[int(frameInHex[1], 16) * 4 * 2:])
    elif frameInHex[18:20] == "11":
        udp(frameInHex[int(frameInHex[1], 16) * 4 * 2:], frameInHex, pcap, frameNum)
    elif frameInHex[18:20] == "01":
        icmp(frameInHex[int(frameInHex[1], 16) * 4 * 2:])


def printIpv4Stats(ipv4Stats):
    print("IP adresy vysielajúcich uzlov:")
    i = 0
    maxS = 0
    while i < len(ipv4Stats):
        print(formatIp(ipv4Stats[i]))
        if ipv4Stats[i + 1] > maxS:
            maxS = ipv4Stats[i + 1]
        i += 2

    print(f"\nAdresa uzla s najväčším počtom odoslaných paketov: \n"
          f"{formatIp(ipv4Stats[ipv4Stats.index(maxS) - 1])}\t{maxS} paketov")


def findInConversations(conversations, frame, index):
    for i in conversations:
        if frame[52:60] in i and frame[60:68] in i:
            i.append(index)
            return True
    return False


def conversationICMP(pcap):

    conversations = []
    for pkt in range(len(pcap)):
        raw = scapy.raw(pcap[pkt])
        frameInHex = raw.hex()
        if frameInHex[24:28] == "0800" and frameInHex[46:48] == "01":
            if not findInConversations(conversations, frameInHex, pkt):
                conversations.append([frameInHex[52:60], frameInHex[60:68], pkt])

    for num in range(len(conversations)):
        print(f"Komunikacia {num + 1}")
        print(f"Total amount of frames in this conversation: {len(conversations[num]) - 2}")
        if len(conversations[num]) - 2 > 20:
            index = 2
            while index < 12:
                frameInHex = scapy.raw(pcap[conversations[num][index]]).hex()
                printAllInfo(frameInHex, None, conversations[num][index] + 1, pcap)
                index += 1
            index = len(conversations[num]) - 10
            while index < len(conversations[num]):
                frameInHex = scapy.raw(pcap[conversations[num][index]]).hex()
                printAllInfo(frameInHex, None, conversations[num][index] + 1, pcap)
                index += 1
        else:
            index = 2
            while index < len(conversations[num]):
                frameInHex = scapy.raw(pcap[conversations[num][index]]).hex()
                printAllInfo(frameInHex, None, conversations[num][index] + 1, pcap)
                index += 1

    # print(conversations)


def findInConvWithPorts(conversations, frame, index, protPosition):
    for i in conversations:
        if frame[52:60] in i and frame[60:68] in i and frame[protPosition: protPosition + 4] in i and frame[protPosition + 4: protPosition + 8] in i:
            i.append(index)
            return True
    return False


def check3wayHandshake(conv, pcap):
    if len(conv) < 8:
        return False

    frame1 = scapy.raw(pcap[conv[5]]).hex()
    frame1ProtPos = 28 + int(frame1[29], 16) * 4 * 2
    flag1 = int(frame1[frame1ProtPos + 26: frame1ProtPos + 28], 16)

    frame2 = scapy.raw(pcap[conv[6]]).hex()
    frame2ProtPos = 28 + int(frame2[29], 16) * 4 * 2
    flag2 = int(frame2[frame2ProtPos + 26: frame2ProtPos + 28], 16)

    frame3 = scapy.raw(pcap[conv[7]]).hex()
    frame3ProtPos = 28 + int(frame3[29], 16) * 4 * 2
    flag3 = int(frame3[frame3ProtPos + 26: frame3ProtPos + 28], 16)

    if flag1 & 0b00000010 and flag2 & 0b00000010 and flag2 & 0b00010000 and flag3 & 0b00010000:
        return True
    else:
        return False


def checkEndConv(conv, pcap):
    if len(conv) < 8:
        return False

    index = 5
    while index < len(conv):
        frame = scapy.raw(pcap[conv[index]]).hex()
        frameProtPos = 28 + int(frame[29], 16) * 4 * 2
        flag = int(frame[frameProtPos + 26: frameProtPos + 28], 16)
        if flag & 0b00000100:
            return True
        if flag & 0b00000001:
            srcPort = frame[frameProtPos: frameProtPos + 4]
            dstPort = frame[frameProtPos + 4: frameProtPos + 8]
            indexTEMP = index + 1
            while indexTEMP < len(conv):
                frameT = scapy.raw(pcap[conv[indexTEMP]]).hex()
                frameProtPosT = 28 + int(frameT[29], 16) * 4 * 2
                flagT = int(frameT[frameProtPosT + 26: frameProtPosT + 28], 16)
                if flagT & 0b00000001 and srcPort == frameT[frameProtPosT + 4: frameProtPosT + 8] and dstPort == frameT[frameProtPosT: frameProtPosT + 4]:
                    return True
                indexTEMP += 1
        index += 1

    return False


def printConvList(conv, pcap, offset):

    print(f"Total amount of frames in this conversation: {len(conv) - offset}")
    if len(conv) - offset > 20:
        index = offset
        while index < 10 + offset:
            frameInHex = scapy.raw(pcap[conv[index]]).hex()
            printAllInfo(frameInHex, None, conv[index] + 1, pcap)
            index += 1
        index = len(conv) - 10
        while index < len(conv):
            frameInHex = scapy.raw(pcap[conv[index]]).hex()
            printAllInfo(frameInHex, None, conv[index] + 1, pcap)
            index += 1
    else:
        index = offset
        while index < len(conv):
            frameInHex = scapy.raw(pcap[conv[index]]).hex()
            printAllInfo(frameInHex, None, conv[index] + 1, pcap)
            index += 1


def convWithConnect(pcap, protocol):
    if protocol == "FTP data":
        protocol = "0014"
    elif protocol == "HTTP":
        protocol = "0050"
    elif protocol == "HTTPS":
        protocol = "01bb"
    elif protocol == "SSH":
        protocol = "0016"
    elif protocol == "FTP CONTROL":
        protocol = "0015"
    elif protocol == "TELNET":
        protocol = "0017"

    conversations = []
    for pkt in range(len(pcap)):
        raw = scapy.raw(pcap[pkt])
        frameInHex = raw.hex()
        if frameInHex[24:28] == "0800" and frameInHex[46:48] == "06":
            protPosition = 28 + int(frameInHex[29], 16) * 4 * 2
            if frameInHex[protPosition: protPosition + 4] == protocol or frameInHex[protPosition + 4: protPosition + 8] == protocol:
                if not findInConvWithPorts(conversations, frameInHex, pkt, protPosition):
                    flag = int(frameInHex[protPosition + 26: protPosition + 28], 16)
                    if flag & 0b00000010:
                        conversations.append([0, frameInHex[52:60], frameInHex[60:68], frameInHex[protPosition: protPosition + 4], frameInHex[protPosition + 4: protPosition + 8], pkt])

    for conv in conversations:
        if check3wayHandshake(conv, pcap):
            conv[0] += 1
        if checkEndConv(conv, pcap):
            conv[0] += 2

    isCompleteWrit = False
    isUnCompleteWrit = False

    for conv in conversations:
        if not isCompleteWrit and conv[0] == 3:
            print("\nComplete conversation: ")
            printConvList(conv, pcap, 5)
            isCompleteWrit = True
        if not isUnCompleteWrit and conv[0] == 1:
            print("\nIncomplete conversation: ")
            printConvList(conv, pcap, 5)
            isUnCompleteWrit = True

    if not isCompleteWrit:
        print("Complete conversation was not found")
    if not isUnCompleteWrit:
        print("Incomplete conversation was not found")

    # print(conversations)


def findInTFTPconv(conversations, frame, index, prtPos):
    for i in conversations:
        if i[0] == frame[52:60] and i[1] == frame[prtPos: prtPos + 4] and i[2] == frame[60:68] and i[3] == frame[prtPos + 4: prtPos + 8]:
            i.append(index)
            return True
        elif i[0] == frame[60:68] and i[1] == frame[prtPos + 4: prtPos + 8] and i[2] == frame[52:60] and i[3] == frame[prtPos: prtPos + 4]:
            i.append(index)
            return True

    return False


def findNextTFTPport(pcap, index, clientAddr, clientPort, serverAddr):

    index += 1
    while index < len(pcap):
        raw = scapy.raw(pcap[index])
        frameInHex = raw.hex()
        if frameInHex[24:28] == "0800" and frameInHex[46:48] == "11":
            protPosition = 28 + int(frameInHex[29], 16) * 4 * 2
            if frameInHex[52:60] == serverAddr and frameInHex[60:68] == clientAddr and frameInHex[protPosition + 4: protPosition + 8] == clientPort:
                return frameInHex[protPosition: protPosition + 4]
        index += 1

    return None


def printWholeConv(pcap, conv, offset):

    for c in conv:
        print(f"Total amount of frames in this conversation: {len(c) - offset}")
        index = offset
        while index < len(c):
            frameInHex = scapy.raw(pcap[c[index]]).hex()
            printAllInfo(frameInHex, None, c[index] + 1, pcap)
            index += 1


def convTFTP(pcap):
    conversations = []

    for pkt in range(len(pcap)):
        raw = scapy.raw(pcap[pkt])
        frameInHex = raw.hex()
        if frameInHex[24:28] == "0800" and frameInHex[46:48] == "11":
            protPosition = 28 + int(frameInHex[29], 16) * 4 * 2
            if frameInHex[protPosition + 4: protPosition + 8] == "0045":
                tftpPort = findNextTFTPport(pcap, pkt, frameInHex[52:60], frameInHex[protPosition: protPosition + 4], frameInHex[60:68])
                conversations.append([frameInHex[52:60], frameInHex[protPosition: protPosition + 4], frameInHex[60:68], tftpPort, pkt])
            else:
                findInTFTPconv(conversations, frameInHex, pkt, protPosition)

    # printWholeConv(pcap, conversations, 4)
    number = 1
    for conv in conversations:
        print(f"Conversation {number}")
        number += 1
        printConvList(conv, pcap, 4)
    # print(conversations)


def findARPinConv(convList, frame):
    if convList[1] == frame[44:56] and convList[2] == frame[56:64] and convList[3] == frame[64:76] and convList[4] == frame[76:84]:
        return True

    return False


def convARP(pcap):
    requests = []
    replies = []
    conversations = []

    for pkt in range(len(pcap)):
        raw = scapy.raw(pcap[pkt])
        frameInHex = raw.hex()
        if frameInHex[24:28] == "0806":
            if frameInHex[40:44] == "0001":
                requests.append(pkt)
            elif frameInHex[40:44] == "0002":
                replies.append(pkt)

    for reqIndex in range(len(requests)):
        if requests[reqIndex] is None:
            reqIndex += 1
            continue
        frameInHex = scapy.raw(pcap[requests[reqIndex]]).hex()
        newConvList = [0, frameInHex[44:56], frameInHex[56:64], frameInHex[64:76], frameInHex[76:84], requests[reqIndex]]
        temp = reqIndex + 1
        while temp < len(requests):
            if requests[temp] is not None:
                frameTEMP = scapy.raw(pcap[requests[temp]]).hex()
                if findARPinConv(newConvList, frameTEMP):
                    newConvList.append(requests[temp])
                    requests[temp] = None
            temp += 1
        for repIndex in range(len(replies)):
            if replies[repIndex] is None:
                repIndex += 1
                continue
            frameTEMP = scapy.raw(pcap[replies[repIndex]]).hex()
            if frameTEMP[56:64] == newConvList[4] and frameTEMP[64:76] == newConvList[1] and frameTEMP[76:84] == newConvList[2]:
                newConvList.append(replies[repIndex])
                newConvList[0] += 1
                replies[repIndex] = None
            repIndex += 1
        conversations.append(newConvList)
        requests[reqIndex] = None
        reqIndex += 1

    # print(conversations)
    # print(requests)
    # print(replies)
    if not conversations:
        print("No ARP couples found")

    count = 1
    for con in conversations:
        if con[0] >= 1:
            print(f"Komunikacia {count}")
            count += 1
            sortedList = sorted(con[5:])
            index = 0
            while index < len(sortedList):
                frameInHex = scapy.raw(pcap[sortedList[index]]).hex()
                printAllInfo(frameInHex, None, sortedList[index] + 1, pcap)
                index += 1

    print("ARP frames without requests or replies: ")
    for con in conversations:
        if con[0] == 0:
            index = 5
            while index < len(con):
                frameInHex = scapy.raw(pcap[con[index]]).hex()
                printAllInfo(frameInHex, None, con[index] + 1, pcap)
                index += 1

    for index in requests:
        if index is not None:
            frameInHex = scapy.raw(pcap[index]).hex()
            printAllInfo(frameInHex, None, index + 1, pcap)

    for index in replies:
        if index is not None:
            frameInHex = scapy.raw(pcap[index]).hex()
            printAllInfo(frameInHex, None, index + 1, pcap)


def formatMAC(string):
    return (f"{string[0:2]} "
            f"{string[2:4]} "
            f"{string[4:6]} "
            f"{string[6:8]} "
            f"{string[8:10]} "
            f"{string[10:12]}")


def printARP(frameInHex):
    if frameInHex[40:44] == "0001":
        print(f"ARP-Request, IP adresa: {formatIp(frameInHex[76:84])}, MAC adresa: ", end="")
        print("???") if frameInHex[64:76] == "000000000000" else print(formatMAC(frameInHex[64:76]))
    elif frameInHex[40:44] == "0002":
        print(f"ARP-Reply, IP adresa: {formatIp(frameInHex[56:64])}, MAC adresa: {formatMAC(frameInHex[44:56])}")
    print(f"Zdrojová IP: {formatIp(frameInHex[56:64])}, Cieľová IP: {formatIp(frameInHex[76:84])}")


def printAllInfo(frameInHex, ipv4Stats, frameNum, pcap):
    print(f"-----------RAMEC {frameNum}-----------")
    if frameInHex[24:28] == "0806":
        printARP(frameInHex)
    printLength(frameInHex)
    frameType = printFrameType(frameInHex)
    printMac(frameInHex)
    printNestedProt(frameType, frameInHex)
    if frameInHex[24:28] == "0800":
        ipv4(frameInHex[28:], ipv4Stats, pcap, frameNum)

    printHexPcap(frameInHex)
    print("")


TFTPportsList = []

etherTypes = [None] * (0xFFFF + 1)
lsaps = [None] * (0xFF + 1)
ipProts = [None] * (0xFF + 1)
tcpPorts = [None] * (0xFFFF + 1)
udpPorts = [None] * (0xFFFF + 1)
icmpTypes = [None] * (0xFF + 1)


def readProtocolTXT():
    fileName = input("Enter name of file with protocols: ")
    while not os.path.isfile(fileName):
        print("File does not exists")
        fileName = input("Enter name of file with protocols: ")

    protocolFile = open(fileName, 'r')
    protFile = protocolFile.read()
    protFile = protFile.splitlines()
    protocolFile.close()

    for j in range(len(protFile)):
        if protFile[j] == "#Ethertypes":
            j = insertProtsInList(protFile, j, etherTypes)
        if protFile[j] == "#LSAPs":
            j = insertProtsInList(protFile, j, lsaps)
        if protFile[j] == "#IP Protocol numbers":
            j = insertProtsInList(protFile, j, ipProts)
        if protFile[j] == "#TCP ports":
            j = insertProtsInList(protFile, j, tcpPorts)
        if protFile[j] == "#UDP ports":
            j = insertProtsInList(protFile, j, udpPorts)
        if protFile[j] == "#ICMP types":
            j = insertProtsInList(protFile, j, icmpTypes)


def main():

    readProtocolTXT()

    fileName = input("Enter file's name: ")
    while not os.path.isfile(fileName):
        print("File does not exists")
        fileName = input("Enter file's name: ")

    pcap = scapy.rdpcap(fileName)
    command = -1

    while command != "0":
        print(f"\n0: end\n"
              f"1: analyze and print all frames with IPv4 statistics at the end\n"
              f"2: analyze and print conversations of the given protocol\n"
              f"3: change file\n")
        command = input("Enter command: ")
        if command == "1":
            ipv4Stats = []
            index = 1
            for pkt in pcap:
                frameInHex = scapy.raw(pkt).hex()
                printAllInfo(frameInHex, ipv4Stats, index, pcap)
                index += 1
            printIpv4Stats(ipv4Stats)
        elif command == "2":
            protocol = input("Enter protocols name: ").upper()
            if protocol == "ICMP":
                conversationICMP(pcap)
            elif protocol == "FTP DATA":
                convWithConnect(pcap, "FTP data")
            elif protocol == "HTTP":
                convWithConnect(pcap, "HTTP")
            elif protocol == "HTTPS":
                convWithConnect(pcap, "HTTPS")
            elif protocol == "SSH":
                convWithConnect(pcap, "SSH")
            elif protocol == "FTP CONTROL":
                convWithConnect(pcap, "FTP CONTROL")
            elif protocol == "TELNET":
                convWithConnect(pcap, "TELNET")
            elif protocol == "TFTP":
                convTFTP(pcap)
            elif protocol == "ARP":
                convARP(pcap)
            else:
                print("Unknown protocol")
        elif command == "3":
            fileName = input("Enter file's name: ")
            while not os.path.isfile(fileName):
                print("File does not exists")
                fileName = input("Enter file's name: ")
            pcap = scapy.rdpcap(fileName)
            TFTPportsList.clear()
        elif command == "0":
            break
        else:
            print("Unknown command")


main()
