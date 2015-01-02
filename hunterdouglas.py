# adapted from https://github.com/tannewt/agohunterdouglas/agohunterdouglas.py
# license from that project included in this repo as well

import time
import socket
import json
import re
import sys
import subprocess
import logging
from colorlog import ColoredFormatter

LOG_LEVEL = logging.ERROR
LOGFORMAT = "%(log_color)s[%(levelname)s] %(asctime)s %(name)s : %(message)s%(reset)s"
LOG = None


def get_log(level=LOG_LEVEL):
  global LOG
  if not LOG:
    formatter = ColoredFormatter(LOGFORMAT)
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logging.root.setLevel(level)
    stream.setLevel(level)
    LOG = logging.getLogger(__name__)
    LOG.addHandler(stream)
    LOG.setLevel(level)
  return LOG

HD_GATEWAY_PORT = 522
TIMEOUT = 10
DB_FILE = "hunterdouglas.json"
TEMP_FILE = "input.txt"
DB = {}


def net_com(message, sentinel=None):
  check_db()
  content = None
  get_log().debug("sending message: %s", message)
  if not 'comtype' in DB or "socket" == DB['comtype']:
    get_log().debug("using socket communication")
    content = socket_com(message, sentinel)
  else:
    get_log().debug("using netcat communication")
    content = nc_com(message, sentinel)
  get_log().debug("received message:")
  get_log().debug(content)
  return content

def socket_com(message, sentinel=None, sock=None):
  content = None
  try:
    if not sock:
      sock = create_socket()
      sock.sendall(message)
      content = recv_until(sock, sentinel)
  except socket.error:
    pass
  finally:
    if sock:
      sock.close()
  return content

def nc_com(message, sentinel=None):
  check_db()
  content = None
  lcmd = ['/usr/bin/nc', '-i2', DB['server'], str(HD_GATEWAY_PORT)]
  get_log().debug("executing %s", lcmd)
  with open(TEMP_FILE, 'w+') as fp:
    fp.write(message+"\n")
  with open(TEMP_FILE, 'r') as fp:  
    content = subprocess.check_output(lcmd, stderr=subprocess.STDOUT, stdin=fp)
  return content

def check_db():
  global DB
  if not "rooms" in DB:
    load_db()

def save_db():
  global DB
  with open(DB_FILE, 'w+') as fp:
    json.dump(DB, fp)

def load_db():
  global DB
  try:
    with open(DB_FILE, 'r') as fp:
      DB = json.load(fp)
  except IOError:
    pass

def set_server(server):
  global DB
  DB['server'] = server
  save_db()

def is_alive(sock):
  return socket_com("$dmy", "ack", sock)

def create_socket():
  global DB
  check_db()

  try:
    sock = socket.create_connection((DB['server'], HD_GATEWAY_PORT), timeout=TIMEOUT)
    helo = recv_until(sock, 'Shade Controller')
  except socket.error:
    sock.close()
    sock = None
  return sock

def set_multi_shade(internal_ids, hd_value):
  # space separated list of ids or array of ids
  if not isinstance(internal_ids, list):
    internal_ids = internal_ids.split(' ')
  for each_id in internal_ids:
    set_shade(each_id, hd_value)
    time.sleep(2)

def set_room(internal_id, hd_value):
  check_db()
  room_ids = []
  for name in DB['shades']:
    shade = DB['shades'][name]
    if internal_id == shade['room']:
      room_ids.append(shade['id'])
  set_multi_shade(room_ids,hd_value)
  return None

def set_shade(internal_id, hd_value):
  sock = create_socket()

  if "up" == hd_value:
    hd_value = 255
  elif "down" == hd_value:
    hd_value = 0
  else:
    if hd_value.isdigit():
      hd_value = min(int(round(int(hd_value)*255.0/100)),255)
    else:
      hd_value = -1
  
  if 0 > hd_value or 255 < hd_value:
    return None

  content = net_com("$pss%s-04-%03d" % (internal_id, hd_value), "done")
  return content + net_com("$rls", "act00-00-")
  
def set_scene(internal_id):
  return net_com("$inm%s-" % (internal_id), "act00-00-")

def recv_until(sock, sentinel=None):
  info = ""
  while True:
    try:
      chunk = sock.recv(1)
    except socket.timeout:
      break
    info += chunk
    if info.endswith(sentinel): break
    if not chunk: break
  return info

def find_by_id(type, id):
  global DB
  check_db()
  for key in DB[type].keys():
    if DB[type][key]['id'] == id:
      return key
  return None

def find_by_name(kind, name):
  global DB
  check_db()
  result = []
  name = name.lower()
  for key in DB[kind].keys():
    if name in DB[kind][key]['search']:
      result.append(DB[kind][key])
  return result  

def init(params=None):
  global DB
  check_db()

  comtype = 'socket'

  if 'comtype' in DB:
    comtype = DB['comtype']

  if params:                 
    # <server-ip> <init-method (alt)>
    params = params.split(' ')
    get_log().debug("processing with params : %s", params)
    if(len(params) > 0):
      set_server(params[0])
    if(len(params) > 1 and 'alt' == params[1]):
      comtype = 'alt'

  DB['comtype'] = comtype


  if not 'server' in DB or not DB['server']:
    msg = "Platinum Gateway IP is not set. Please set it using pl_update <ip>"
    return msg

  sock = create_socket()
  if not sock:
    msg = "Cannot reach Platinum Gateway. Please recheck IP and set"
    return msg
  else:
    sock.close()

  info = net_com("$dat", "upd01-")
  if not info:
    msg = "Unable to get data about windows and scenes from Gateway"
    return msg

  DB['rooms'] = {}
  DB['scenes'] = {}
  DB['shades'] = {}

  prefix = None
  lines = re.split(r'[\n\r]+', info)

  for line in lines:
    line = line.strip()
    if not prefix:
      prefix = line[:2]
    elif not line.startswith(prefix):
      continue
    else:
      line = line[2:]

    if line.startswith("$cr"):
      # name of room
      room_id = line[3:5]
      room_name = line.split('-')[-1].strip()
      DB['rooms'][room_name] = {'name':room_name, 'id':room_id, 'search':room_name.lower()}
    elif line.startswith("$cm"):
      # name of scene
      scene_id = line[3:5]
      scene_name = line.split('-')[-1].strip()
      DB['scenes'][scene_name] = {'name':scene_name, 'id':scene_id, 'search':scene_name.lower()}
    elif line.startswith("$cs"):
      # name of a shade
      parts = line.split('-')
      shade_id = line[3:5]
      shade_name = parts[-1].strip()
      room_id = parts[1]
      DB['shades'][shade_name] = {'name':shade_name, 'id':shade_id, 'search':shade_name.lower(), 'room': room_id}
    elif line.startswith("$cp"):
      # state of a shade
      shade_id = line[3:5]
      state = line[-4:-1]
      state = str(int((int(state) / 255.) * 16))
      shade = find_by_id('shades',shade_id)
      if shade:
        DB['shades'][shade]['state'] = state
  save_db()
  return "Window Cache Updated"

def main():
  get_log(logging.DEBUG)
  print init(" ".join(sys.argv[1:]))

if __name__ == "__main__":
    main()
  