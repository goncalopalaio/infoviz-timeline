import bimpy
from PIL import Image
import concurrent.futures
import threading
import queue

def log(text):
	print("log :: %s" % (text))

class MessagePipeline:
	def __init__(self):
		# thread safe queue
		self.queue = queue.Queue(maxsize = 1000)
		# Event object to notify queue has changed
		self.event = threading.Event()

class Data:
	def __init__(self):
		self.text = ""

def thread_message_consumer_func(data, thread_message_pipeline):
	log("Starting thread_message_consumer_func")

	while True:
		while thread_message_pipeline.event.is_set():
			if thread_message_pipeline.queue.empty():
				log("thread_message_consumer_func :: nothing on queue")
				break

			while not thread_message_pipeline.queue.empty():
				message = thread_message_pipeline.queue.get()
				log("Message is %s" % (message))

				if(message == "exit"):
					log("thread_message_consumer_func :: exiting")
					return
				data.text = str(message) + "\n" + data.text

		log("thread_message_consumer_func :: clearing event flag")
		thread_message_pipeline.event.clear()

		log("thread_message_consumer_func :: waiting")
		thread_message_pipeline.event.wait()

def send_messages(pipeline, messages):
	log("send_messages :: starting")
	for m in messages:
		pipeline.queue.put(m)
		pipeline.event.set()
	log("send_messages :: finished")

def main():
	ctx = bimpy.Context()
	ctx.init(800, 800, "Image")

	data = Data()

	thread_message_pipeline = MessagePipeline()
	thread_message_consumer = threading.Thread(target = thread_message_consumer_func, args = (data, thread_message_pipeline, ))
	
	thread_message_consumer.start()
	#image = Image.open("3.png")
	#im = bimpy.Image(image)

	while not ctx.should_close():
		with ctx:
			bimpy.set_next_window_pos(bimpy.Vec2(120, 120), bimpy.Condition.Once)
			bimpy.set_next_window_size(bimpy.Vec2(400, 400), bimpy.Condition.Once)
			bimpy.begin("Window #1")
			
			bimpy.text("This is text!")
			
			if bimpy.button("Send A Lot Of Messages"):
				temp_messages = ["Message#" + str(i) for i in range(560)]
				send_messages(thread_message_pipeline, temp_messages)

			if bimpy.button("Send Exit Message"):
				send_messages(thread_message_pipeline, ["exit"])

			bimpy.text("Text from events:\n%s" % (data.text))

			bimpy.end()
			#bimpy.image(im)

	log("Exited rendering thread")

	log("Sending exit to thread_message_consumer")
	send_messages(thread_message_pipeline, ["exit"])

	log("Waiting for thread_message_consumer")
	thread_message_consumer.join()

	log("Bye")

if __name__ == '__main__':
	main()