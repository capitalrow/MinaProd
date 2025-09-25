# services/logger.py
import logging, json, sys
from datetime import datetime

class _JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "lvl": record.levelname,
            "msg": record.getMessage(),
            "name": record.name,
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)

def configure_logging(json_logs: bool = False):
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.INFO)
    h.setFormatter(_JsonFormatter() if json_logs else logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(h)