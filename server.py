import bimpy
from PIL import Image
import concurrent.futures
import threading
import queue
import random

def log(text):
	print("log :: %s" % (text))

temp_separation_test = bimpy.Float(0.5)

class MessagePipeline:
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

def thread_message_consumer_func(data, thread_message_pipeline):
	log("Starting thread_message_consumer_func")

	while True:
		while thread_message_pipeline.event.is_set():
			if thread_message_pipeline.queue.empty():
				log("thread_message_consumer_func :: nothing on queue")
				break

			while not thread_message_pipeline.queue.empty():
				message = thread_message_pipeline.queue.get()
				log("Message is %s" % (str(message.idd)))

				if message.idd == "exit":
					log("thread_message_consumer_func :: exiting")
					return
				if message.idd == "log":
					data.text = str(message.text) + "\n" + data.text
				elif message.idd == "point":
					data.points.append(message.point)


		log("thread_message_consumer_func :: clearing event flag")
		thread_message_pipeline.event.clear()

		log("thread_message_consumer_func :: waiting")
		thread_message_pipeline.event.wait()

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

	bimpy.slider_float("separation", temp_separation_test, 0.0, 100.0)

	bimpy.end()

def main():
	ctx = bimpy.Context()
	ctx.init(1200, 1200, "Image")
	with ctx:
		bimpy.themes.set_light_theme()

	data = Data()

	thread_message_pipeline = MessagePipeline()
	thread_message_consumer = threading.Thread(target = thread_message_consumer_func, args = (data, thread_message_pipeline, ))
	
	thread_message_consumer.start()
	
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
				send_messages(thread_message_pipeline, temp_messages)
			
			if bimpy.button("Send A Lot Of Random Points"):
				temp_messages = [make_message_point("point", i, i) for i in range(20)]
				send_messages(thread_message_pipeline, temp_messages)				
			
			if bimpy.button("Clear Flag"):
				clear_flag = not clear_flag
			
			bimpy.text("Text from events:\n%s" % (data.text))

			bimpy.end()

			draw_window_drawing(ctx, 400, 400, "Sample Drawing", [])

	log("Exited rendering thread")

	log("Sending exit to thread_message_consumer")
	send_message_text(thread_message_pipeline, "exit", "")

	log("Waiting for thread_message_consumer")
	thread_message_consumer.join()

	log("Bye")

if __name__ == '__main__':
	main()