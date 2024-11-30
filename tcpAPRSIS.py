#!/usr/bin/env python3
import asyncio
from ax253 import Frame
import aprs

import db_functions

aprs.__author__ = "KD9YQK"
aprs.__distribution__ = "kiss3_async.py"
aprs.__version__ = "1.00"

import js8Modem


def get_aprs_pw(callsign: str):
    cs = callsign.upper()
    i = 0
    tmp_code = 29666
    while i < len(cs):
        tmp_code = tmp_code ^ ord(cs[i]) * 256
        tmp_code = tmp_code ^ ord(cs[i + 1])
        i += 2
    tmp_code = tmp_code & 32767
    return tmp_code


def pad_callsign(callsign: str):
    pad = 9 - len(callsign)
    retval = callsign
    for n in range(0, pad):
        retval += ' '
    print(f'*{retval}*')
    return retval


class igate_params:
    # host = "noam.aprs2.net"
    host = '205.209.228.99'
    port = 14580
    password = ""
    enabled = False
    tx_enabled = False
    filter_dist = "5000"
    filter_params = "t/m"
    filter = ""

    def set_igate_filter(self, _callsign=''):
        # self.filter = f"{self.filter_params}/{callsign}/{self.filter_dist}"
        self.filter = f"{self.filter_params}"  # /{self.filter_dist}"


class APRSIS:
    MYCALL: str
    SSID: str
    PATH = ['WIDE1-1', 'WIDE2-1']
    LAT = "4145.  N/"
    LON = "08818.  W?"
    COMMENT = 'Ham-Microblog Server https://github.com/KD9YQK/ham-microblog'

    tx_buffer = []
    tx_en = True
    pos_enabled = True

    igate_protocol = None
    ig = igate_params()

    def __init__(self, callsign="HAMBLG"):
        self.MYCALL = callsign
        self.ig.password = get_aprs_pw(callsign)
        self.ig.set_igate_filter(_callsign=callsign)

    async def igate_rx(self, callback=None):
        while True:
            async for frame in self.igate_protocol.read():
                if callback:
                    await callback(frame)
                else:
                    print("igate")
                    print(frame)

    async def igate_tx(self, interval=1.0):
        while True:
            if len(self.tx_buffer) > 0:
                msg = self.tx_buffer[0]
                self.tx_buffer.pop(0)
                frame = Frame.ui(
                    destination='ADZ666',
                    source=msg['src'],
                    path=self.PATH,
                    info=msg['info'],
                )
                self.igate_protocol.write(frame)
            await asyncio.sleep(interval)

    async def send_pos(self, delay=600):
        await asyncio.sleep(10)
        while True:
            msg = {
                'src': self.MYCALL,
                'dest': 'ADZ666',
                'info': f'={self.LAT}{self.LON}{self.COMMENT}'
            }
            self.tx_buffer.append(msg)
            await asyncio.sleep(delay)

    async def setup(self, rx_callback=None):
        print("Connecting to aprs-is")
        transport, self.igate_protocol = await aprs.create_aprsis_connection(
            host=self.ig.host,
            port=self.ig.port,
            user=self.MYCALL,
            passcode=self.ig.password,
            command=f'filter {self.ig.filter}',
        )
        print('Connected!')
        rx = asyncio.create_task(self.igate_rx(rx_callback))
        tx = asyncio.create_task(self.igate_tx(interval=1.0))
        return rx, tx

    async def main(self):
        _rx, _tx = await self.setup()
        while True:
            await asyncio.sleep(1)

    async def rx_callback(self, frame: Frame):
        frm = str(frame)
        callsign_ssid = str(frame.source)
        callsign = callsign_ssid
        if '-' in callsign:
            callsign = callsign.split('-')[0]
        frm = frm.split('::')[1]
        target = frm.split(':')[0].strip()
        if target != 'HAMBLG':
            print(frame)
            return
        msg = frm.split(':')[1]
        msgid = ""
        if '{' in msg:
            msgid = msg.split('{')[1]
            msg = msg.split('{')[0]
        tx_msg = {'src': target, 'info': f':{pad_callsign(callsign_ssid)}:ack{msgid}'}
        self.tx_buffer.append(tx_msg)
        cmd = msg.split(' ')[0]
        if cmd == js8Modem.Command.GET_POSTS:
            post = db_functions.get_callsign_blog(msg.split(' ')[1], 1)
            tx_msg['info'] = f':{pad_callsign(callsign_ssid)}:{js8Modem.Command.POST} ' \
                             f'{post["callsign"]} {post["time"]} {post["msg"]}'
            self.tx_buffer.append(tx_msg)
        elif cmd == js8Modem.Command.POST:
            try:
                mtime = int(msg.split(' ')[1])
                post = msg.split(str(mtime))[1].strip()
                db_functions.add_blog(mtime, callsign, post)
            except ValueError:
                return


if __name__ == "__main__":
    # print(get_aprs_pw('HAMBLG'))


    async def m():
        t: APRSIS = APRSIS('HAMBLG')
        _a, _b = await t.setup(t.rx_callback)
        while True:
            await t.send_pos(600)


    try:
        asyncio.run(m())
    except KeyboardInterrupt:
        exit()