from dataclasses import dataclass
from typing import Generic, Hashable, Optional, TypeVar


K = TypeVar("K", bound=Hashable, contravariant=True)
V = TypeVar("V")


@dataclass
class Message(Generic[K, V]):
    key: K
    value: Optional[V] = None
