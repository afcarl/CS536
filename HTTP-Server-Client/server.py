import socket
import argparse
import threading
import os.path
import time
import stat

HOST = 'localhost'

proto_v = "HTTP/1.0"

chunk_size = 4096

img_formats = ['.jpeg', '.jpg', '.png']

def parse():
	parser = argparse.ArgumentParser()
	parser.add_argument('port',type=int)
	return parser.parse_args()

def response_header(content_len,c_type='text/plain',last_modified=None):
	header = {
		'Content-Type' : '{}'.format(c_type),
		'Content-Length': str(content_len),
	}

	if last_modified is not None:
		header['Last-Modified'] = last_modified

	return ''.join('%s: %s\n' % (k, v) for k, v in header.iteritems())

'''
	Return something like this:
	HTTP/1.0 200 OK
'''
def response_status(status_code,status_txt):
	return proto_v + ' ' + str(status_code) + ' ' + status_txt + '\n'


def parse_filename(request):
	filename =  request.split(' ')[1][1:]
	if not filename:
		filename = 'index.html' 

	return filename

def head(request):
	if request[0:4] == 'HEAD':
		return True
	return False

def isValidRequest(request):
	if not request:
		return False
	command = request.split()[0]
	if command == 'HEAD' and command == 'GET':
		return True

	protocol = request.split()[2]
	if protocol == 'HTTP/1.0' or protocol == 'HTTP/1.1':
		return True

	return False

def serve_client(request,conn):
	
	if not isValidRequest(request):
		response = response_status(400,'Bad Request'+'\r\n')
		conn.send(response)
		conn.close()
		return

	filename = parse_filename(request)
	_,filext = os.path.splitext(filename)

	filetype = None

	if filext in img_formats:
		filetype = 'image/{}'.format(filext[1:])
	if filext == '.html' or filext == '.htm':
		filetype = 'text/html'
	if filext == '.txt':
		filetype = 'text/plain'

	if not filetype:
		response = response_status(404,'File Not Found') + response_header(0,filetype)
		conn.send(response)
		conn.close()
		return
	
	filepath = "Upload/{}".format(filename)

	if not os.path.exists(filepath):
		response = response_status(404,'File Not Found') + response_header(0,filetype)
		conn.send(response+'\r\n')
		conn.close()
		return

	st = os.stat(filepath)
	if not bool(st.st_mode & stat.S_IROTH):
		response = response_status(403,"Forbidden") + response_header(0,filetype)
		conn.send(response+'\r\n')
		conn.close()
		return

	# Read the file and send
	f = open(filepath,'r').read()

	# send the response header
	file_len = len(f)
	# If no filetye assigned, send a 404 error, our server only identifies these types of files

	# get the last modified information for the requested file
	timestamp = os.path.getmtime(filepath)
	timestamp = time.strftime("%a, %d %b %Y %H:%M:%S +0000",time.gmtime(timestamp))

	response = response_status(200,'OK') + response_header(file_len,filetype,timestamp)

	# '\n' Indicates the beginning of the response body
	conn.send(response+'\r\n')
	
	if head(request):
		conn.close()
		return

	left = file_len
	while left > 0:
		s = min(left,chunk_size)
		conn.send(f[:s])
		f = f[s:]
		left = left - s


	conn.close()

if __name__ == "__main__":

	args = parse()
	PORT = args.port

	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
	s.bind((HOST,PORT))
	s.listen(5)

	while 1:
		conn,addr = s.accept()
		request = conn.recv(1024)
		t = threading.Thread(target=serve_client,args=(request,conn,))
		t.start()
 