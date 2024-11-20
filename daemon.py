import db_functions
import js8Modem
import tcpModem
import asyncio
import json
import threading


class Daemon:
    tcpmodem: tcpModem.ClientProtocol
    js8modem: js8Modem.JS8modem
    settings: dict

    async def process_outgoing(self):
        while True:
            await asyncio.sleep(1)
            print('ok')
            msgs = db_functions.get_outgoing_posts()
            for m in msgs:
                if self.settings['js8modem']:
                    self.js8modem.broadcast_post(m)
                if self.settings['tcpmodem']:
                    _t = {'type': tcpModem.types.ADD_BLOG, 'value': m}
                    self.tcpmodem.send_msg(json.dumps(_t).encode())

    def start_tcpmodem(self, host='157.230.203.194', port=8808):
        loop: asyncio.AbstractEventLoop = asyncio.AbstractEventLoop()
        try:
            loop = asyncio.get_event_loop()
            coro = loop.create_connection(tcpModem.ClientProtocol, host=host, port=port)
            _listen = loop.create_task(self.process_outgoing())
            _server = loop.run_until_complete(coro)
            self.tcpmodem = tcpModem.clients[0]

            # data = {"type": tcpModem.types.GET_ALL_MSGS, "value": {"callsign": "KD9YQK"}}
            # self.tcpmodem.send_msg(json.dumps(data).encode())
        except ConnectionRefusedError:
            print("TCP/IP ERROR - Unable to connect to TCP Server")
            return
        except KeyboardInterrupt:
            exit()
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            exit()

    def start_js8modem(self, host='127.0.0.1', port=2442):
        try:
            self.js8modem = js8Modem.JS8modem(host=host, port=port)
            self.js8modem.start()
            # while self.js8modem.js8call.online:
            #    pass
        except RuntimeError:
            print("JS8Call ERROR - JS8Call application not installed or connection issue")
            return
        except KeyboardInterrupt:
            exit()


if __name__ == "__main__":
    settings = db_functions.get_settings()
    daemon = Daemon()
    daemon.settings = settings

    threads = []
    # JS8Call Modem Thread
    if settings['js8modem']:
        threads.append(threading.Thread(target=daemon.start_js8modem(), args=()).start())

    # TCP Modem Thread
    if settings['tcpmodem']:
        threads.append(threading.Thread(target=daemon.start_tcpmodem(), args=()).start())

    # APRS Modem Thread
    if settings['aprsmodem']:
        pass

    # for t in threads:
    #    t.start()
    # for t in threads:
    #    t.join()
