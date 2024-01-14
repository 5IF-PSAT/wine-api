import logging


class RequestHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)

    def emit(self, record):
        self.format(record)
        date = record.msg['date']
        time = record.msg['time']
        message = record.msg['message']
        path = record.msg['path']
        response_time = record.msg['response_time']
        method = record.msg['method']
        status_code = record.msg['status_code']
        self.stream.write(f'{date},{time},{method},{path},{response_time},{message},{status_code}\n')
        self.flush()