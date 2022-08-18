import logging
from typing import Any, Optional

LOG = logging.getLogger(__name__)

try:
    import ujson as json
except ImportError:
    LOG.debug("ujson module not found, using json")
    import json

_NOT_SET = object()


class BaseSerializer:
    DEFAULT_ENCODING: Optional[str] = "utf-8"

    def __init__(self, *args, encoding=_NOT_SET, **kwargs):
        self.encoding = self.DEFAULT_ENCODING if encoding is _NOT_SET else encoding
        super().__init__(*args, **kwargs)

    def dumps(self, value: Any) -> str:
        raise NotImplementedError("dumps method must be implemented")

    def loads(self, value: str) -> Any:
        raise NotImplementedError("loads method must be implemented")


class JsonSerializer(BaseSerializer):
    def dumps(self, value):
        return json.dumps(value)

    def loads(self, value):
        if value is None:
            return None
        return json.loads(value)
