from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

limiter  = Limiter(key_func=get_remote_address, storage_uri="memory://")
cache    = Cache(config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})
csrf     = CSRFProtect()