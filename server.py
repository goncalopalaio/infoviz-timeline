import bimpy
from PIL import Image
import concurrent.futures
import threading
import queue
import random
import time
from shoes import shoes

temp_separation_test = bimpy.Float(0.5)

def log(text):
	print("log :: %s" % (text))


class MessagePipeline(object):
	def __init__(self):
		# thread safe queue
		self.queue = queue.Queue(maxsize = 1000)
		# Event object to notify queue has changed
		self.event = threading.Event()


class Message:
	def __init__(self):
		self.idd = None
		self.text = None
		self.point = None


class Data:
	def __init__(self):
		self.text = ""
		self.points = []

class ServerCtx:
	def __init__(self):
		self.message_pipeline = MessagePipeline()
		self.data = Data()

		self.server_socket = None
		self.server_socket_running = True

CTX = ServerCtx()

def thread_socket_func(port):
	global CTX
	sock=shoes.Server("0.0.0.0", port)
	sock.listen()

	CTX.server_socket = sock

	while CTX.server_socket_running:
		#time.sleep(1)
		#sock.sendall("Hello!")
		dropped = []
		for s in sock.connections:
			conn, info = s
			log("thread_socket_func :: Waiting for receive")
			message = sock.receive(conn)

			log("thread_socket_func :: Received             :: message '%s'" % (repr(message)))
			if message == 'exit' or message == 'exit\n' or message == 'exit\r\n':
				log("thread_socket_func :: Exit message received")
				conn.close()
				dropped.append(s)
			parse_socket_message(CTX.message_pipeline, message)

		for d in dropped:
			sock.connections.remove(d)
			sock.user_count -= 1

	# log("thread_socket_func :: Stop listening")
	# sock.stoplisten()
	log("thread_socket_func :: Closing connections")
	for s, info in sock.connections:
		log("thread_socket_func :: Closing %s" % (str(info)))
		s.close()

	

	log("thread_socket_func :: Exiting")

def message_thread_func():
	global CTX
	log("Starting message_thread_func")

	while True:
		while CTX.message_pipeline.event.is_set():
			if CTX.message_pipeline.queue.empty():
				log("message_thread_func :: nothing on queue")
				break

			while not CTX.message_pipeline.queue.empty():
				message = CTX.message_pipeline.queue.get()
				log("Message is %s" % (str(message.idd)))

				if message.idd == "exit":
					log("message_thread_func :: exiting")
					return
				if message.idd == "log":
					CTX.data.text = str(message.text) + "\n" + CTX.data.text
				elif message.idd == "point":
					CTX.data.points.append(message.point)


		log("message_thread_func :: clearing event flag")
		CTX.message_pipeline.event.clear()

		log("message_thread_func :: waiting")
		CTX.message_pipeline.event.wait()

def parse_socket_message(pipeline, message):
	if "point" in message:
		s = message.split(" ")
		x = int(s[1])
		y = int(s[2])

		send_message_point(pipeline, 'point', x, y)
def make_message_text(idd, text):
	m = Message()
	m.idd = idd
	m.text = text
	return m

def make_message_point(idd, point):
	m = Message()
	m.idd = idd
	m.point = point
	return m

def send_message_point(pipeline, idd, x, y):
	log("send_message :: starting")
	
	message = make_message_point(idd, (x, y))

	pipeline.queue.put(message)
	pipeline.event.set()
	log("send_message :: finished")


def send_message_text(pipeline, idd, text):
	log("send_message :: starting")
	
	message = make_message_text(idd, text)

	pipeline.queue.put(message)
	pipeline.event.set()
	log("send_message :: finished")

def send_messages(pipeline, messages):
	log("send_messages :: starting")
	for m in messages:
		pipeline.queue.put(m)
		pipeline.event.set()
	log("send_messages :: finished")

def draw_window_drawing(ctx, w, h, name, points):

	bimpy.set_next_window_pos(bimpy.Vec2(w + 20, h + 20), bimpy.Condition.Once)
	bimpy.set_next_window_size(bimpy.Vec2(w, h), bimpy.Condition.Once)
	bimpy.begin(name)
	
	window_zero = bimpy.get_window_pos() + bimpy.Vec2(100 + temp_separation_test.value, 100 + temp_separation_test.value)
	window_one = bimpy.get_window_pos() + bimpy.Vec2(w - 100 - temp_separation_test.value, h - 100 - temp_separation_test.value)
	
	bimpy.add_circle_filled(window_zero, 5.0, 0xFF000000 + 0xc88200, 100)
	bimpy.add_circle_filled(window_one, 5.0, 0xFF000000 + 0x4bb43c, 100)

	for x,y in points:
		point = bimpy.get_window_pos() + bimpy.Vec2(x, y)
		bimpy.add_circle_filled(point, 5.0, 0xFF000000 + 0x4bb43c, 100)


	bimpy.slider_float("separation", temp_separation_test, 0.0, 100.0)

	bimpy.end()

def main():
	global CTX

	ctx = bimpy.Context()
	ctx.init(1200, 1200, "Image")
	with ctx:
		bimpy.themes.set_light_theme()


	socket_thread = threading.Thread(target = thread_socket_func, args = (8883, ))
	socket_thread.start()

	message_thread = threading.Thread(target = message_thread_func)
	message_thread.start()

	previous_n_points = 0
	clear_flag = False
	while not ctx.should_close():
		with ctx:
			bimpy.set_next_window_pos(bimpy.Vec2(120, 120), bimpy.Condition.Once)
			bimpy.set_next_window_size(bimpy.Vec2(400, 400), bimpy.Condition.Once)
			bimpy.begin("Window #1")
			
			bimpy.text("This is text!")
			
			if bimpy.button("Send A Lot Of Messages"):
				temp_messages = [make_message_text("log", "Message #" + str(i)) for i in range(560)]
				send_messages(CTX.message_pipeline, temp_messages)
			
			if bimpy.button("Send A Lot Of Random Points"):
				temp_messages = [make_message_point("point", (random.randrange(400 + i), random.randrange(400 + i))) for i in range(20)]
				send_messages(CTX.message_pipeline, temp_messages)				
			
			if bimpy.button("Clear Flag"):
				clear_flag = not clear_flag
			
			bimpy.text("Text from events:\n%s" % (CTX.data.text))

			bimpy.end()

			draw_window_drawing(ctx, 400, 400, "Sample Drawing", CTX.data.points)

	log("Exited rendering thread")

	log("Sending exit to message_thread")
	send_message_text(CTX.message_pipeline, "exit", "")

	log("Waiting for message_thread")
	message_thread.join()
	CTX.server_socket_running = False
	if CTX.server_socket:
		for c, info in CTX.server_socket.connections:
			c.send(b'exit')

	log("Waiting for socket_thread")
	socket_thread.join()

	log("Bye")

if __name__ == '__main__':
	main()