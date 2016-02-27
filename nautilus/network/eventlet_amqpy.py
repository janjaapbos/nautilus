""" eventlet based AMQP handling
using amqpy (easy_install3 amqpy),
see https://github.com/veegee/amqpy


This is not in working state yet. Just took stuff from earlier
testing with eventlet / amqpy.

The idea is that for incoming HTTP requests that need to be forwarded
through AMQP something will be done like this:


from nautilus.network.eventlet_amqpy import AmqpyRequest

def parse_env(env):
    r = {}
    for k in [
        'REQUEST_METHOD', 'PATH_INFO', 'SERVER_PROTOCOL', 'HTTP_USER_AGENT',
        'REMOTE_PORT', 'SERVER_NAME', 'REMOTE_ADDR', 'SERVER_PORT', 'HTTP_HOST',
        'HTTP_ACCEPT', 'RAW_PATH_INFO', 'GATEWAY_INTERFACE',
        'CONTENT_TYPE', "QUERY_STRING",
    ]:
        r[k] = env.get(k)
    return r

def hello_world(environ, start_response):
    env = parse_env(environ)
    path = env['PATH_INFO']
    if not path.startswith("/route/"):
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['Not Found. Try /route/test.server/my_resource/\r\n']
    route = path[7:]
    routing_key = route.split("/")[0]

    query_args = None
    if environ['REQUEST_METHOD'] == 'POST':
        post_env = environ.copy()
    if environ['REQUEST_METHOD'] == 'POST':
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        post = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=post_env,
            keep_blank_values=True
        )
        query_args = {}
        for key in post.keys():
            query_args[key] = post[key].value

    evt = eventlet.event.Event()
    AmqpyRequest(routing_key=routing_key, route=route, evt=evt, env=env,
              query_args=query_args).send()
    timeout = eventlet.Timeout(300)
    try:
        msg = evt.wait()
    except eventlet.Timeout as t:
        if t is not timeout:
            raise "Not my timeout"
        start_response('500 Error', [('Content-Type', 'text/plain')])
        return ['Request Timeout!\r\n']
    timeout.cancel()
    start_response('200 OK', [('Content-Type', 'application/json')])
    return [msg.body + "\r\n"]


"""

import eventlet
eventlet.import_patched("amqpy")
from amqpy import Connection, Message, AbstractConsumer
import uuid

REPLY_TO = str(uuid.uuid4())


conn = Connection()  # connect to guest:guest@localhost:5672 by default


class AmqpyRequestQueue:

    def __init__(self, send_channel, send_exchange):
        self.send_channel = send_channel
        self.send_exchange = send_exchange
        self.queue = {}

    def send(self, amqpyRequest):
        amqpyRequest.msg = Message(
            amqpyRequest.request,
            correlation_id=amqpyRequest.correlation_id,
            reply_to=REPLY_TO,
        )
        self.queue[amqpyRequest.correlation_id] = amqpyRequest
        res = self.send_channel.basic_publish(
            amqpyRequest.msg,
            exchange=self.send_exchange,
            routing_key=amqpyRequest.routing_key
        )

    def receive(self, msg):
        msg.ack()
        correlation_id = msg.properties.get("correlation_id")
        if not correlation_id:
            print('Unknown message: {}'.format(msg.body))
            return
        try:
            amqpyRequest = self.queue.pop(correlation_id)
        except KeyError:
           print 'Unknown correlation_id: {}'.format(correlation_id)
           return
        amqpyRequest.onResponse(msg)

ch_requests = conn.channel()
amqpyRequestQueue = AmqpyRequestQueue(ch_requests, "test.exchange")


class AmqpyRequest:
    _correlation_id = None
    finished = False
    routing_key = None
    method = "GET"
    route = "test.server/users/"
    url_params = None
    query_args = None
    body_args = None
    headers = None
    repeat = False
    repeat_interval = 5

    def __init__(
            self, routing_key=routing_key, method=method, route=route, url_params=url_params,
            query_args=query_args, body_args=body_args, headers=headers, repeat=repeat,
            evt=None, env=None):
        self.routing_key = routing_key
        self.method = method
        self.route = route
        self.url_params = url_params
        self.query_args = query_args
        self.body_args = body_args
        self.headers = headers
        self.repeat = repeat
        self.evt = evt
        self.env = env

        print "self.route", self.route
        if self.query_args is None and self.env.get("QUERY_STRING"):
            self.query_args = urlparse.parse_qs(
                self.env.get("QUERY_STRING"),
                keep_blank_values=True,
            )

    @property
    def correlation_id(self):
        if not self._correlation_id:
            self._correlation_id = str(uuid.uuid4())
        return self._correlation_id

    def finish(self):
        self.finished = True
        del amqpyRequestQueue[self.correlation_id]

    @property
    def request(self):
         return json.dumps(
             dict(
                 method=self.method,
                 route=self.route,
                 url_params=self.url_params,
                 query_args=self.query_args,
                 body_args=self.body_args,
                 headers=self.headers,
                 env=self.env
            )
        )

    def send(self):
        amqpyRequestQueue.send(self)

    def onResponse(self, msg):
        print "onResponse", self.correlation_id, msg.properties.get("correlation_id")
        print('Response message: {}'.format(msg.body))
        self.evt.send(msg)
        if self.repeat:
            self.start_repeat_timer()

    def start_repeat_timer(self, repeat_interval=repeat_interval):
         if repeat_interval:
            self.repeat_interval = repeat_interval
         threading.Timer(self.repeat_interval, self.repeat_thread, ()).start()

    def repeat_thread(self):
        if self.finished:
            return
        self.send()


class RequestResponseConsumer(AbstractConsumer):
    def run(self, msg):
        amqpyRequestQueue.receive(msg)

ch_request_response = conn.channel()
ch_request_response.exchange_declare('test.exchange', 'direct')
ch_request_response.queue_declare(REPLY_TO)
ch_request_response.queue_bind(REPLY_TO, exchange='test.exchange', routing_key=REPLY_TO)

request_response_consumer = RequestResponseConsumer(ch_request_response, REPLY_TO)
request_response_consumer.declare()



class ServiceRequestConsumer(AbstractConsumer):
    def __init__(self, service):
        self.service = service
        ch = conn.channel()
        ch.exchange_declare('test.exchange', 'direct')
        ch.queue_declare(self.service.name)
        ch.queue_bind(REPLY_TO, exchange='test.exchange', routing_key=service.name)

        AbstractConsumer.__init__(self, ch, service.name)
        self.declare()

    def run(self, msg):
        #TODO
        # Here we get the AMQP message that must be processed by the Flask 
        # service app


def drain(conn):
    # wait for events, which will receive delivered messages and call any consumer callbacks
    while True:
        print "draining"
        conn.drain_events(timeout=None)

eventlet.spawn_n(drain, conn)
