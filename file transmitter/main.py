# Developed in PyCharm, python 3.9
import copy
import socket
import multiprocessing
import time
import libscrc
import sys
import os
import select

MAX_FRAGMENT_SIZE = 1426
TIMEOUT = 5
ENTER_PATH_TIMEOUT = 180
MAX_RETRANSMISSIONS = 3
ERROR_FRAGMENT_NUM = 5

_WRQ = 1
_DATA = 2
_ACK = 3
_RRQ = 4
_KCRQ = 5
_ERROR = 6
_SWITCH = 7
_FIN = 8

_cur_retransmissions = 0


class Packet:
    checksum = 0
    data = None

    def __init__(self, opcode, fragment_num, data):
        self.opcode = opcode
        self.fragment_num = fragment_num
        self.data = data
        self.calc_checksum()

    def calc_checksum(self):
        if self.data is not None:
            self.checksum = libscrc.buypass(self.opcode.to_bytes(1, 'big') + self.fragment_num.to_bytes(3, 'big') + self.data)
        else:
            self.checksum = libscrc.buypass(self.opcode.to_bytes(1, 'big') + self.fragment_num.to_bytes(3, 'big'))

    def encode(self):
        if self.data is None:
            return self.opcode.to_bytes(1, 'big') + self.fragment_num.to_bytes(3, 'big') + self.checksum.to_bytes(2, 'big')
        else:
            return self.opcode.to_bytes(1, 'big') + self.fragment_num.to_bytes(3, 'big') + self.data + self.checksum.to_bytes(2, 'big')


def send_packet(socket_this, packet, address_receiver):
    global ERROR_FRAGMENT_NUM
    # print(f"Sending opcode {packet.opcode}")

    if packet.fragment_num == ERROR_FRAGMENT_NUM and packet.opcode == _DATA:
        copy_packet = copy.deepcopy(packet)
        copy_packet.data += int(1).to_bytes(1, 'big')
        ERROR_FRAGMENT_NUM = -1
        socket_this.sendto(copy_packet.encode(), address_receiver)
    else:
        socket_this.sendto(packet.encode(), address_receiver)


def packet_decode(packet):
    return Packet(int.from_bytes(packet[:1], 'big'), int.from_bytes(packet[1:4], 'big'), packet[4:len(packet) - 2])


def safe_receive_packet(socket_this, address_receiver, received_packet, timeout):
    while True:
        ready = select.select([socket_this], [], [], timeout)
        if not ready[0]:
            return False
        else:
            raw_received_packet = None
            ip = None
            try:
                raw_received_packet, ip = socket_this.recvfrom(1500)
            except:
                return False
            decoded_packet = packet_decode(raw_received_packet)
            if decoded_packet.opcode != _WRQ and decoded_packet.opcode != _DATA:
                received_packet[0] = decoded_packet
                return True
            print(f"Packet received. Opcode: {decoded_packet.opcode}. ", end="")
            if decoded_packet.fragment_num != 0:
                print(f"Fragment #{decoded_packet.fragment_num}. ", end="")
            print(f"Fragment size: {len(decoded_packet.data)}. ", end="")
            print(f"Checksum ", end="")
            if libscrc.buypass(raw_received_packet) != 0:
                print('\033[91m' + "WRONG" + '\033[0m')
                send_packet(socket_this, Packet(_RRQ, decoded_packet.fragment_num, None), address_receiver)
                received_packet[0] = None
                return True
            else:
                print('\33[32m' + "OK" + '\033[0m')
                # send_packet(socket_this, Packet(_ACK, decoded_packet.fragment_num, None), address_receiver)
                received_packet[0] = decoded_packet
                return True


def receiving_role_new(socket_this, address_receiver):
    received_packet = [None]
    file_name = None
    path_name = [None]
    message = "Message: \n"
    is_first = True
    result = multiprocessing.Manager().list([None])
    prev_packet = None
    clear_socket(socket_this)
    while True:
        while True:  # receive first packet

            if is_first:
                if safe_receive_packet(socket_this, address_receiver, received_packet, ENTER_PATH_TIMEOUT) is False:
                    print(f"Timeout exceeded, returning to menu...")
                    return

            if received_packet[0] is None:
                continue

            if received_packet[0].opcode == _WRQ:
                file_name = received_packet[0].data.decode()
                print(f"FILE NAME: {file_name}")

                while True:
                    path_name[0] = input('Enter path to save the file ("Enter" to save in current directory): ')
                    if os.path.isdir(path_name[0]):
                        file_name = os.path.join(path_name[0], file_name)
                        break
                    elif len(path_name[0]) == 0:
                        break
                    else:
                        print("Directory does not exist!")

                send_packet(socket_this, Packet(_ACK, 0, None), address_receiver)

                while True:  # send ACK when user entered the file path and wait for the data packet
                    if safe_receive_packet(socket_this, address_receiver, received_packet, TIMEOUT * (MAX_RETRANSMISSIONS + 2)) is False:
                        print(f"Timeout exceeded, returning to menu...")
                        return

                    if received_packet[0].opcode == _DATA: # потім послати ACK
                        break
                break

            if received_packet[0].opcode == _DATA:
                message = "Message: \n"
                file_name = None
                message += received_packet[0].data.decode()
                send_packet(socket_this, Packet(_ACK, received_packet[0].fragment_num, None), address_receiver)
                prev_packet = received_packet[0].fragment_num
                while True:

                    if safe_receive_packet(socket_this, address_receiver, received_packet, TIMEOUT * (MAX_RETRANSMISSIONS + 2)) is False:
                        print(f"Timeout exceeded, connection terminated")
                        return

                    if received_packet[0] is None:
                        continue

                    if received_packet[0].fragment_num == prev_packet:  # if the ACK was not received by opposite side
                        send_packet(socket_this, Packet(_ACK, 0, None), address_receiver)
                        continue

                    break
                break

        file = None
        if file_name is not None:
            file = open(file_name, "wb")

        total_frag_num = 0

        while True:
            if received_packet[0].opcode == _KCRQ:
                send_packet(socket_this, Packet(_ACK, 0, None), address_receiver)
                break

            if file is not None:
                file.write(received_packet[0].data)
            else:
                message += received_packet[0].data.decode()

            send_packet(socket_this, Packet(_ACK, received_packet[0].fragment_num, None), address_receiver)
            prev_packet = received_packet[0].fragment_num
            while True:

                if safe_receive_packet(socket_this, address_receiver, received_packet, TIMEOUT * (MAX_RETRANSMISSIONS + 2)) is False:
                    print(f"Timeout exceeded, connection terminated")
                    return

                total_frag_num += 1

                if received_packet[0] is None:
                    continue

                if received_packet[0].fragment_num == prev_packet:
                    # print("The same")
                    send_packet(socket_this, Packet(_ACK, received_packet[0].fragment_num, None), address_receiver)
                    continue

                break

        if file is not None:
            print("File successfully received")
            print(f"Total number of received fragments: {total_frag_num}, from which {prev_packet} are correct")
            print(f"Absolute file path: {os.path.abspath(file_name)}")
            file.close()
        else:
            print("Message successfully received")
            print(f"Total number of received fragments: {total_frag_num + 1}, from which {prev_packet} are correct")
            print(message)

        fn = sys.stdin.fileno()
        command_process = multiprocessing.Process(target=get_command, args=(fn, result))
        command_process.start()

        while True:

            if safe_receive_packet(socket_this, address_receiver, received_packet, TIMEOUT * (MAX_RETRANSMISSIONS + 2)) is False:
                print("Timeout exceeded, connection terminated")
                command_process.kill()
                return

            if not command_process.is_alive():
                if result[0] == "0":
                    send_packet(socket_this, Packet(_FIN, 0, None), address_receiver)
                    return
                elif result[0] == "1":
                    send_packet(socket_this, Packet(_SWITCH, 0, None), address_receiver)
                    return "switch"

            elif received_packet[0].opcode == _FIN:
                print("Other side terminated the connection. Returning to the menu...")
                command_process.kill()
                return

            elif received_packet[0].opcode == _KCRQ:
                send_packet(socket_this, Packet(_ACK, 0, None), address_receiver)

            elif received_packet[0].opcode == _WRQ or received_packet[0].opcode == _DATA:
                print("")
                command_process.kill()
                is_first = False
                break


def clear_socket(socket_this):
    while True:
        ready = select.select([socket_this], [], [], 0.5)
        if not ready[0]:
            break
        else:
            socket_this.recv(1500)


def controller(socket_this, address_receiver):
    while True:
        print("\n0: exit\n"
              "1: receive\n"
              "2: send\n"
              "3: change listening port\n"
              "4: change receiving side")
        command = input("Enter command: ")

        while True:
            reset_retrans_num()
            if command == "2":
                if sending_role_new(socket_this, address_receiver) == "switch":
                    command = "1"
                else:
                    break
            elif command == "1":
                if receiving_role_new(socket_this, address_receiver) == "switch":
                    command = "2"
                else:
                    break
            elif command == "0":
                return
            elif command == "3":
                socket_this = set_listening_port(socket_this)
                break
            elif command == "4":
                address_receiver = set_other_side()
                break
            else:
                print("Invalid command")
                break


def get_command(fn, results):
    sys.stdin = os.fdopen(fn)
    while True:
        print("\n0: return to menu\n"
              "1: switch")
        results[0] = input("Enter command: ")
        if results[0] == "0":
            print("returning to menu...")
        if results[0] == "1":
            print("switching...")
        if results[0] == "0" or results[0] == "1":
            break
        else:
            print("There is no such option!\n")


def receive_ACK_timeout(socket_this, address_receiver, received_opcode, timeout):
    while True:
        # print("waiting for packet...")
        ready = select.select([socket_this], [], [], timeout)
        if not ready[0]:
            return False
        else:
            raw_received_packet = None
            ip = None
            try:
                raw_received_packet, ip = socket_this.recvfrom(1500)
            except:
                return False
            decoded_packet = packet_decode(raw_received_packet)
            if ip == address_receiver:
                # print("RECEIVED ACK")
                received_opcode[0] = decoded_packet.opcode
                return True


def are_retransmissions_exceeded():
    global _cur_retransmissions

    if _cur_retransmissions == MAX_RETRANSMISSIONS:
        reset_retrans_num()
        return True

    _cur_retransmissions += 1
    return False


def reset_retrans_num():
    global _cur_retransmissions
    _cur_retransmissions = 0


def send_message(socket_this, address_receiver, message, received_opcode, fragment_size):
    sent_frag_num = 0
    fragment_num = 1
    while True:
        fragment_data = message[((fragment_num - 1) * fragment_size):(fragment_size * fragment_num)]
        if not fragment_data:
            print(f"Total number of sent fragments: {sent_frag_num}, from which {fragment_num - 1} fragments were received correctly")
            return True
        packet_to_send = Packet(_DATA, fragment_num, fragment_data.encode())
        fragment_num += 1
        while True:  # waiting for the ACK packet
            received_opcode[0] = None
            send_packet(socket_this, packet_to_send, address_receiver)
            sent_frag_num += 1
            print(f"Sending fragment #{packet_to_send.fragment_num} Size: {len(packet_to_send.data)}")

            if receive_ACK_timeout(socket_this, address_receiver, received_opcode, TIMEOUT) is False:  # the answer packet was not received
                if are_retransmissions_exceeded():
                    print("Auto-retransmission number exceeded, connection terminated")
                    return False
                print("Timeout exceeded, resending packet...")
                continue

            reset_retrans_num()

            if received_opcode[0] == _RRQ:
                print("fragment was received with wrong checksum! resending...")
                continue
            if received_opcode[0] == _ACK:
                print("fragment was successfully transmitted!")
                break


def send_file(socket_this, address_receiver, file_name, received_opcode, fragment_size):
    file_name_extracted = os.path.basename(file_name)
    print("waiting when other side enters the path...")
    while True:  # waiting for the first ACK
        received_opcode[0] = None
        send_packet(socket_this, Packet(1, 0, file_name_extracted.encode()), address_receiver)

        if receive_ACK_timeout(socket_this, address_receiver, received_opcode, ENTER_PATH_TIMEOUT) is False:  # the answer packet was not received
            if are_retransmissions_exceeded():
                print("Auto-retransmission number exceeded, can not connect")
                return False
            print("Timeout exceeded, resending packet...")
            continue

        reset_retrans_num()

        if received_opcode[0] == _ACK:
            break

    fragment_num = 1
    sent_frag_num = 0
    with open(file_name, "rb") as file:
        while True:
            fragment_data = file.read(fragment_size)
            if not fragment_data:
                print(f"Total number of sent fragments: {sent_frag_num}, from which {fragment_num - 1} fragments were received correctly")
                return True
            packet_to_send = Packet(2, fragment_num, fragment_data)
            fragment_num += 1
            while True:  # waiting for the ACK packet
                received_opcode[0] = None
                # print(packet_to_send.fragment_num)
                send_packet(socket_this, packet_to_send, address_receiver)
                sent_frag_num += 1
                print(f"Sending fragment #{packet_to_send.fragment_num} Size: {len(packet_to_send.data)}")

                if receive_ACK_timeout(socket_this, address_receiver, received_opcode, TIMEOUT) is False:  # the answer packet was not received
                    if are_retransmissions_exceeded():
                        print("Auto-retransmission number exceeded, connection terminated")
                        return False
                    print("Timeout exceeded, resending packet...")
                    continue

                reset_retrans_num()

                if received_opcode[0] == _RRQ:
                    print("fragment was received with wrong checksum! resending...")
                    continue
                if received_opcode[0] == _ACK:
                    print("fragment was successfully transmitted!")
                    break


def get_command_send(fn, results):
    sys.stdin = os.fdopen(fn)
    while True:
        print(f"\n"
              f"0: return to main menu\n"
              f"1: send file\n"
              f"2: send message")

        data_type = input("Enter command: ")
        if data_type == "0":
            results[0] = 0
            print("Returning to menu...")
            return
        elif data_type == "1":
            results[0] = 1
            file_name = input("Enter file's name: ")
            while not os.path.isfile(file_name):
                print("File does not exists")
                file_name = input("Enter file's name: ")
            results[1] = file_name
            break
        elif data_type == "2":
            results[0] = 2
            message = input("Enter message: ")
            results[1] = message
            break
        else:
            print("There is no such option!")

    fragment_size = int(input(f"Enter fragment size (1 - {MAX_FRAGMENT_SIZE}): "))
    while fragment_size > MAX_FRAGMENT_SIZE or fragment_size <= 0:
        print("Enter valid size!")
        fragment_size = int(input(f"Enter fragment size (1 - {MAX_FRAGMENT_SIZE}): "))

    results[2] = fragment_size


def sending_role_new(socket_this, address_receiver):
    clear_socket(socket_this)

    file_name = None
    message = None
    data_type = None
    results = multiprocessing.Manager().list([None, None, None])
    received_opcode = multiprocessing.Manager().list([None])

    while True:
        data_type = input("Message or file?: ").upper()
        if data_type == "FILE":
            file_name = input("Enter file's name: ")
            while not os.path.isfile(file_name):
                print("File does not exists")
                file_name = input("Enter file's name: ")
            break
        elif data_type == "MESSAGE":
            message = input("Enter message: ")
            break
        else:
            print("There is no such option!")

    fragment_size = int(input(f"Enter fragment size (1 - {MAX_FRAGMENT_SIZE}): "))
    while fragment_size > MAX_FRAGMENT_SIZE or fragment_size <= 0:
        print("Enter valid size!")
        fragment_size = int(input(f"Enter fragment size (1 - {MAX_FRAGMENT_SIZE}): "))

    while True:
        if data_type == "MESSAGE":
            if not send_message(socket_this, address_receiver, message, received_opcode, fragment_size):
                return
        elif data_type == "FILE":
            if not send_file(socket_this, address_receiver, file_name, received_opcode, fragment_size):
                return
            else:
                print(f"Absolute file path: {os.path.abspath(file_name)}")

        fn = sys.stdin.fileno()
        command_process = multiprocessing.Process(target=get_command_send, args=(fn, results))
        command_process.start()

        packet_to_send = Packet(_KCRQ, 0, None)
        while True:
            received_opcode[0] = None
            send_packet(socket_this, packet_to_send, address_receiver)

            if receive_ACK_timeout(socket_this, address_receiver, received_opcode, TIMEOUT) is False:  # the answer packet was not received
                if are_retransmissions_exceeded():
                    command_process.kill()
                    print("Auto-retransmission number exceeded, connection terminated")
                    return
                print("Timeout exceeded, resending packet...")
                continue

            reset_retrans_num()

            if not command_process.is_alive():
                break

            if received_opcode[0] == _SWITCH:
                command_process.kill()
                print("\nswitching...")
                return "switch"

            if received_opcode[0] == _FIN:
                print("\nOther side terminated the connection. Returning to the menu...")
                command_process.kill()
                return

            if received_opcode[0] == _ACK:
                time.sleep(TIMEOUT)

        if results[0] == 0:
            send_packet(socket_this, Packet(_FIN, 0, None), address_receiver)
            return

        if results[0] == 1:
            data_type = "FILE"
            file_name = results[1]
            fragment_size = results[2]
            continue

        if results[0] == 2:
            data_type = "MESSAGE"
            message = results[1]
            fragment_size = results[2]
            continue


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def set_listening_port(socket_this):
    socket_this.close()
    socket_this = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            t = (get_ip(), int(input("Enter port: ")))
            socket_this.bind(t)
            return socket_this
        except:
            print('\033[91m' + 'Cannot bind the socket' + '\033[0m')


def set_other_side():
    ip = None
    port = None

    while True:
        try:
            ip = input("Enter IP of receiving side: ")
            socket.inet_aton(ip)
            break
        except:
            print('\033[91m' + 'IP is not valid' + '\033[0m')

    port = int(input("Enter port of receiving side: "))

    return ip, port


if __name__ == '__main__':
    def main():
        print(f"This PC's IP address: {get_ip()}")
        socket_this = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # сокет згенерується сам

        print("Set listening port on this device")
        socket_this = set_listening_port(socket_this)
        address_opposite_side = set_other_side()

        controller(socket_this, address_opposite_side)

        socket_this.close()


    main()



