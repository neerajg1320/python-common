import pika
import os
import time
from pika.exceptions import AMQPConnectionError


def receive_queue_messages(queue_name, message_handler=None, debug=False):

    connected = False
    while not connected:
        qs_host = os.environ.get('QS_HOST')
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=qs_host))
            connected = True
        except AMQPConnectionError as e:
            time.sleep(1)

    print('Connected to queues at host {}'.format(qs_host))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=message_handler, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


def send_queue_message(queue_name, message, debug=False):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.environ.get('QS_HOST')))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)

    body = message if message else 'Hello World!'

    channel.basic_publish(exchange='', routing_key=queue_name, body=body)
    if debug:
        print("{}: sent msg='{}'".format(queue_name, message))

    connection.close()