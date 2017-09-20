import argparse
import os.path
import socket

chunk_size = 4096

def parse():
	parser = argparse.ArgumentParser()

	parser.add_argument('server_host')
	parser.add_argument('server_port',type=int)
	parser.add_argument('filename',nargs='?',default='')
	parser.add_argument('command',choices=['GET',"HEAD"])
	return parser.parse_args()


def createDownloadFolder():
	if not os.path.exists('Download'):
		os.makedirs('Download')


def create_request(args):

	filename = args.filename

	if filename == '/':
		filename = ''
	command = args.command
	if command == 'GET':
		return "GET /{} HTTP/1.0\n\n".format(filename)
	else:
		return "HEAD /{} HTTP/1.0\n\n".format(filename)

def error(header):

	code = int(header.split(' ')[1])

	if code != 200:
		return True
	
	return False

if __name__ == "__main__":

	args = parse()
	HOST = args.server_host
	PORT = args.server_port

	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.connect((HOST,PORT))

	# Get the argument

	request = create_request(args)

	s.sendall(request)

	# read the first response for header	

	header = s.recv(1024)

	true_header = header.split('\r\n')[0]

	print true_header

	body = [header.split('\r\n')[1]]
	# If HEAD request, save the response to file_HEAD.txt
	if args.command == 'HEAD':
		f = open('Download/file_HEAD.txt','a')
		f.write(header.rstrip()+'\n\n')
		s.close()
		exit()

	# If not 200, terminate the client
	if error(header):
		s.close()
		exit()

	msg_len = int(header.split("Content-Length")[1].split('\n')[0].split(':')[1])

	body = []

	recvd = 0

	while recvd < msg_len:
		chunk = s.recv(min(msg_len - recvd,chunk_size))
		# print chunk
		if not chunk:
			raise RuntimeError("Socket Connection Broken")
		body.append(chunk)
		recvd = recvd + len(chunk)

	# Save the file to downloads folder
	# If downloads folder is not present, make the folder
	if not os.path.exists('Download'):
		os.makedirs('Download')

	if args.filename == '' or args.filename == '/':
		f = open('Download/index.html','w')
	else:
		f = open('Download/'+args.filename,'w')
	content = ''
	for chunk in body:
		content = content + chunk
	f.write(content)
	s.close()