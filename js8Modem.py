import pyjs8call
import db_functions
import time


class cmd:  # Commands. Note the space.
    GET_POSTS = ' POSTS?'
    POST = ' POST'


# Numbers transmit slow then letters in JS8Call.
numVal = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E', '6': 'F', '7': 'G', '8': 'H', '9': 'I',
          '0': 'J'}  # Convert Numbers to Letters
abcVal = {'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5', 'F': '6', 'G': '7', 'H': '8', 'I': '9',
          'J': '0'}  # Convert Letters back to Numbers


def num_to_abc(num: int):  # Convert an integer to a string of Letters
    tmp = str(num)
    retval = ''
    for l in tmp:
        retval += numVal[l]
    return retval


def abc_to_num(abc: str):  # Convert a string of Letters Back to Numbers
    tmp = ''
    for l in abc:
        tmp += abcVal[l]
    return int(tmp)


def shrink_timecode(timecode: int):  # Strip the first 5 digits of a timecode. Used to make TX smaller
    tmp = num_to_abc(timecode)
    return tmp[-6:]


def expand_timecode(timecode: str):  # Return the first 5 digits and return a timecode number
    t = int(time.time())
    tmp = str(t)[:4]
    for l in timecode:
        tmp += abcVal[l]
    return int(tmp)


class JS8modem:
    js8call: pyjs8call.Client

    def __init__(self, host='127.0.0.1', port=2442):
        self.js8call = pyjs8call.Client(host=host, port=port)
        self.js8call.callback.register_command(cmd.GET_POSTS, self.cb_get_posts)
        self.js8call.callback.register_command(cmd.POST, self.cb_rcv_post)
        self.js8call.callback.register_incoming(self.cb_incoming)
        self.js8call.callback.register_spots(self.cb_new_spots)

        print("* Js8Call Modem Initialized.")
        print(f"* Host: {host} * Port: {port}")

    def start(self):
        self.js8call.start()
        self.js8call.inbox.enable()

    ###########################################
    # Custom Callbacks
    ###########################################
    def cb_incoming(self, msg):  # Test callback when any msg is received
        pass
        #print(f" * From: {msg.origin} To: {msg.destination} Message: {msg.text}")

    def cb_new_spots(self, spots):  # Callback when a new spot is received.
        for spot in spots:
            if spot.grid in (None, ''):
                grid = ' '
            else:
                grid = ' (' + spot.grid + ') '

            #print('\t--- Spot: {}{}@ {} Hz\t{}L'.format(spot.origin, grid, spot.offset,
            #                                            time.strftime('%x %X', time.localtime(spot.timestamp))))

    def cb_get_posts(self, msg):  # Callback when the POSTS? command is received
        # do not respond in the following cases:
        if (
                self.js8call.settings.autoreply_confirmation_enabled() or
                not self.js8call.msg_is_to_me(msg) or  # not directed to local station or configured group
                msg.text in (None, '')  # message text is empty
        ):
            return
        # collect recent posts and format to faster string format
        blog = db_functions.get_callsign_blog(self.js8call.settings.get_station_callsign(), 1)
        if len(blog) < 1:
            return
        message = f"POST {shrink_timecode(blog[0]['time'])} {blog[0]['msg']}"

        # respond to origin station with directed message
        self.js8call.send_directed_message(msg.origin, message)

    def cb_rcv_post(self, msg):
        # do not respond in the following cases:
        if (msg.text in (None, '')):  # message text is empty
            return
        t = msg.text.split('POST ')[1].split(' ')[0]
        msg = msg.text.split('POST ')[1].split(f'{t} ')[1]
        db_functions.add_blog(expand_timecode(t), msg.origin, msg)

    def broadcast_post(self, post: dict, dest = '@BLOG'):
        self.js8call.send_directed_message(dest, message=f"POST {shrink_timecode(post['time'])} {post['msg']}")


if __name__ == '__main__':
    modem: JS8modem
    try:
        modem = JS8modem()
        modem.start()

        # Loop Forever
        while modem.js8call.online:
            pass

    except RuntimeError:
        print("ERROR - JS8Call application not installed or connection issue")
        exit()