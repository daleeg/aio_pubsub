from typing import Callable, Awaitable

SubHandler = Callable[[tuple[str, str]], Awaitable[None]]
