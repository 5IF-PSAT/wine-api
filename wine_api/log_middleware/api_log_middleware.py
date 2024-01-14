import logging
import datetime
import time


def log_request(obj, request, logger_req):
    request_time = datetime.datetime.now()
    now_date = request_time.strftime("%Y-%m-%d")
    now_time = request_time.strftime("%H:%M:%S.%f")
    start_time = time.time()
    response = obj.get_response(request)
    duration = time.time() - start_time
    response_ms = duration * 1000
    method = str(getattr(request, 'method', '')).upper()
    status_code = str(getattr(response, 'status_code', ''))
    request_path = request.get_full_path()
    if '200' <= status_code < '400':
        logger_req.info({
            "date": str(now_date),
            "time": str(now_time),
            "message": '',
            "path": request_path,
            "response_time": str(response_ms),
            "method": method,
            "status_code": status_code
        })
    elif '400' <= status_code <= '500':
        logger_req.error({
            "date": str(now_date),
            "time": str(now_time),
            "message": '',
            "path": request_path,
            "response_time": str(response_ms),
            "method": method,
            "status_code": status_code
        })
    return response


logger = logging.getLogger(__name__)


class APILogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = log_request(self, request, logger)
        return response