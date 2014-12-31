# adapted from https://github.com/tannewt/agohunterdouglas/agohunterdouglas.py
# license from that project included in this repo as well

import time
import socket
import json
import re
import sys
import subprocess

HD_GATEWAY_PORT = 522
TIMEOUT = 100
DB_FILE = "hunterdouglas.json"
DB = {}
DEBUG = False

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
  alive = False
  try:
    sock.sendall("$dmy")
    recv_until(sock, "ack\n\r")
    alive = True
  except socket.error as e:
    sock.close()
  return alive

def verify_socket(sock=None):
  global DB
  check_db()

  try:
    if not sock or not is_alive(sock):
      sock = socket.create_connection((DB['server'], HD_GATEWAY_PORT), TIMEOUT)
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
  sock = verify_socket()

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

  sock.sendall("$pss%s-04-%03d" % (internal_id, hd_value))
  recv_until(sock, "done")
  sock.sendall("$rls")
  recv_until(sock, "act00-00-")
  sock.close()
  return True

def set_scene(internal_id):
  sock = verify_socket()
  for i in (1,2):
    sock.sendall("$inm%s-" % (internal_id))
    recv_until(sock, "act00-00-")
    time.sleep(2)
  sock.close()
  return True

def recv_until(sock, sentinel):
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
    #print("searching {candidate} for {key}".format(candidate=DB[kind][key]['search'],key=name))
    if name in DB[kind][key]['search']:
      result.append(DB[kind][key])
  return result  

def init(params=None):
  init_method = 'socket'

  if 'init_method' in DB:
    init_method = DB['init_method']

  if params:                 
    # <server-ip> <init-method (alt)>
    params = params.split(' ')
    if(len(params) > 0):
      set_server(params[0])
    if(len(params) > 1 and 'alt' == params[1]):
      init_method = 'alt'

  DB['init_method'] = init_method

  check_db()

  if not 'server' in DB:
    msg = "Platinum Gateway IP is not set. Please set it using pl_update <ip>"
    return msg

  sock = verify_socket()
  if not sock:
    msg = "Cannot reach Platinum Gateway. Please recheck IP and set"
    return msg
  if 'socket' == init_method:
    sock.sendall("$dat")
    info = recv_until(sock,"upd01-")
    sock.close()
  else:
    lcmd = ['/usr/bin/nc', '-i2', DB['server'], str(HD_GATEWAY_PORT)]
    #print "executing ", lcmd
    inp = open('input.txt')
    info = subprocess.check_output(lcmd, stderr=subprocess.STDOUT, stdin=inp)
    #print "init: {line}".format(line=info)

  DB['rooms'] = {}
  DB['scenes'] = {}
  DB['shades'] = {}

  prefix = None
  lines = re.split(r'[\n\r]+', info)

  for line in lines:
    #print "init: {line}".format(line=line)
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
  global DEBUG
  DEBUG = True
  print init(" ".join(sys.argv[1:]))

if __name__ == "__main__":
    main()
  