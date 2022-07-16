import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

def execute(cmd):
	cmd = cmd.strip()

	if (not cmd):
		return

	output = subprocess.check_output(shlex.split(cmd), stderr = subprocess.STDOUT)
	return output.decode()


class NetCat():
	def __init__(self, args, buffer = None):
		self.args = args
		self.buffer = buffer

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


	def run(self):
		if (self.args.listen):
			self.listen()

		else:
			self.send()


	def handleResponse(self):
		try:
			while (True):
				recvLen = 1
				response = ""

				while (recvLen):
					data = self.socket.recv(4096)
					recvLen = len(data)
					response += data.decode()

					if (recvLen < 4096):
						break

				if (response):
					print("\r" + response, end = "")

		except KeyboardInterrupt:
			print("> User terminated")
			self.socket.close()
			sys.exit()


	def send(self):
		self.socket.connect((self.args.target, self.args.port))

		if (self.buffer):
			self.socket.send(self.buffer)

		handleThread = threading.Thread(target = self.handleResponse)
		handleThread.start()

		while (True):
			buffer = input("")
			buffer += "\n"

			self.socket.send(buffer.encode())


	def listen(self):
		self.socket.bind((self.args.target, self.args.port))
		self.socket.listen(5)

		while (True):
			clientSock, _ = self.socket.accept()
			args = [clientSock]
			clientThread = threading.Thread(target = self.handle, args = args)
			args.append(clientThread)

			clientThread.start()


	def handle(self, clientSock, thread):
		if (self.args.execute):
			output = execute(self.args.execute)
			clientSock.send(output.encode())

		elif (self.args.command):
			cmdBuff = b""

			while (True):
				try:
					clientSock.send(b"\nNerCodeNet's shell > ")

					while ("\n" not in cmdBuff.decode()):
						cmdBuff += clientSock.recv(64)

					response = execute(cmdBuff.decode())

					if (response):
						clientSock.send(response.encode())

					cmdBuff = b""

				except Exception as e:
					print(f"Server killed {e}")
					clientSock.close()
					thread._stop()


if (__name__ == "__main__"):
	parser = argparse.ArgumentParser(description = "NerCodeNet's net tool", formatter_class = argparse.RawDescriptionHelpFormatter, epilog = textwrap.dedent('''hey there!''')) 
	parser.add_argument("-c", "--command", action = "store_true", help = "command shell")
	parser.add_argument("-e", "--execute", help = "execute special command")
	parser.add_argument("-l", "--listen", action = "store_true", help = "listen")
	parser.add_argument("-p", "--port", type = int, default = 5555, help = "special port")
	parser.add_argument("-t", "--target", default = "192.168.1.203", help = "special IP")

	args = parser.parse_args()

	buffer = ""

	nc = NetCat(args, buffer.encode())
	nc.run()