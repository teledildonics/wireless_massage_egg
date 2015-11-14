#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  wme_tx.py
#
#  Copyright 2015 IKARUS
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#


import argparse
from subprocess import Popen, call, DEVNULL
from time import sleep
from os import mkfifo, remove
from sys import exit


# Config.
GRC_FILE_NAME   = './wme_tx_gr'
FIFO_FILE       = './packets-fifo.bin'


def generate_packet(command, repeat=4):
  """
  Generate a packet according to the command parameter and repeat it
  according to the repeat parameter.
  """
  packet = ''
  if command.lower() == 'off':
    packet = '1111001011001011011001001011011001011001001001011001'
  elif command.lower() == 'up':
    packet = '1111001011001011011001001011011011011001011011001001'
  elif command.lower() == 'down':
    packet = '1111001011001011011001001011001011011001011001011001'
  else:
    print("Invalid command '{}'".format(command))
    return None

  # Repeat the packet.
  packet += '0000' # Space between two packages.
  packet *= repeat
  raw_packet = bytes([int(b) for b in packet])
  return raw_packet


def packet_to_fifo(packet, file_name=FIFO_FILE):
  """
  Save packet to the FIFO file. The FIFO will be read by the
  gnuradio script.
  """
  with open(file_name, 'wb') as output:
    output.write(packet)


def make_fifo(file_name=FIFO_FILE):
  """
  Create FIFO file to communicate with gnuradio.
  """
  try:
    mkfifo(FIFO_FILE)
  except FileExistsError:
    pass


def launch_gr(ignore_output=True):
  """
  Launch the python script created from the GRC flowgraph.
  If the script does not exist, create it from the .grc file.
  """
  try:
    if ignore_output:
      sdr = Popen(GRC_FILE_NAME + '.py', stdout=DEVNULL, stderr=DEVNULL)
    else:
      sdr = Popen(GRC_FILE_NAME + '.py')
  except FileNotFoundError:
    # Create script from .grc file.
    print('[-] gnuradio script not found. Creating script from .grc file.')
    if ignore_output:
      call(['grcc', '-d', '.', GRC_FILE_NAME + '.grc'], stdout=DEVNULL, stderr=DEVNULL)
      sdr = Popen(GRC_FILE_NAME + '.py', stdout=DEVNULL, stderr=DEVNULL)
    else:
      call(['grcc', '-d', '.', GRC_FILE_NAME + '.grc'])
      sdr = Popen(GRC_FILE_NAME + '.py')
  return sdr


def main():
  """
  Parse arguments, boot everything up, create packages, send them
  and shut down everything.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("-g", "--grcoutput", action="store_false",
                      help="Show the output of gnuradio/grcc.")
  parser.add_argument("-r", "--repeat", type=int, default=4,
                      help="Repeat every packet REPEAT times. Default is 4.")
  parser.add_argument("-c", "--command", type=str, required=True,
                      help="Remote control command. Commands are 'up', 'down' or 'off'. "
                           "Use 'up' to turn it on.")
  args = parser.parse_args()

  # Check params (e.g. repeat > 0).
  if args.repeat < 0:
    print("Invalid repeat count '{}'".format(args.repeat))
    exit(1)
  if args.command != 'up' and args.command != 'down' and args.command != 'off':
    print("Invalid command '{}'".format(args.command))
    exit(2)

  # Boot up everything.
  print('[+] Create FIFO file to communicate with gnuradio.')
  make_fifo()
  print('[+] Launch gnuradio script to send packages from the FIFO file.')
  sdr = launch_gr(args.grcoutput)
  print('[+] Wait 1 second for gnuradio to boot up.')
  sleep(1)
  print('[+] Every packet will be repeated {} times.'.format(args.repeat))

  # Create the packages.
  packages = generate_packet(args.command, args.repeat)

  # Send the packages.
  try:
    # Each symbol takes 0.0006s. A packet has 52 symbols and 4 symbols of spacing.
    # Each packet will be repeated args.repeat times.
    send_time = round(len(packages) * 0.0006 * (args.repeat + 1), 3)
    print('[+] Sending packets... This will take about {} seconds.'.format(send_time))
    packet_to_fifo(packages)
    sleep(send_time)

  except KeyboardInterrupt:
    print('\n[+] Got keyboard interrupt.')

  finally:
    if sdr:
      print('[+] Wait 1 second before terminating gnuradio.')
      sleep(1)
      print('[+] Terminate gnuradio.')
      sdr.terminate()
    print('[+] Remove fifo file.')
    remove(FIFO_FILE)

  print('[+] Exit.')
  return 0


if __name__ == '__main__':
  main()

