import logging, json, datetime

class SocketHandler(logging.Handler):

    def __init__(self, log_list, log_event):
        logging.Handler.__init__(self)
        self.log_list = log_list
        self.log_event = log_event

    def emit(self, record):
        log_entry = self.format(record)
        print("new log from wherever: {}".format(log_entry))
        self.log_list.append(log_entry)
        self.log_event.set()


class WebSocketFormatter(logging.Formatter):
    def __init__(self, task_name=None):
        self.task_name = task_name

        super(WebSocketFormatter, self).__init__()

    def format(self, record):
        data = {'@message': record.msg,
                '@timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                '@type': 'IronWorker'}

        if self.task_name:
            data['@task_name'] = self.task_name

        return json.dumps(data)