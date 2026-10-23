"""Exact question cache, NOT semantic cache; bounded, scoped, versioned."""
import hashlib
import json
import time
import unicodedata
from collections import OrderedDict
from copy import deepcopy
from threading import Lock

class AnswerCache:
    def __init__(self, ttl_seconds=300, capacity=128):
        self.ttl, self.capacity = ttl_seconds, capacity
        self.items, self.lock = OrderedDict(), Lock()

    @staticmethod
    def key(question, user_id, source_version, model_id):
        normalized = ' '.join(unicodedata.normalize('NFKC',question).casefold().split())
        value = [normalized,user_id,source_version,model_id,'evidence-v1']
        return hashlib.sha256(json.dumps(value,ensure_ascii=False).encode()).hexdigest()

    def get(self, key):
        with self.lock:
            item = self.items.get(key)
            if not item: return None
            expires, value = item
            if expires <= time.monotonic():
                del self.items[key]
                return None
            self.items.move_to_end(key)
            return deepcopy(value)

    def put(self, key, value):
        with self.lock:
            self.items[key] = (time.monotonic()+self.ttl,deepcopy(value))
            self.items.move_to_end(key)
            while len(self.items)>self.capacity: self.items.popitem(last=False)
