import json
from itertools import repeat
from typing import IO, Iterator, Sequence, Tuple

from jsonpath_ng.ext import parse
from pipe import chain, map, sort

from flatehr.sources.base import Key, Source, Value

JsonPath = str


class JsonPathSource(Source):
    def __init__(self, input_file: IO, paths: Sequence[JsonPath]):
        self._json = json.load(input_file)
        self._paths = paths

    def iter(self) -> Iterator[Tuple[Key, Value]]:

        mappings = (
            self._paths
            | map(lambda path: list(zip(repeat(path), parse(path).find(self._json))))
            | chain
            | sort(lambda el: str(el[1].full_path))
            | map(
                lambda el: (
                    el[0],
                    None if isinstance(el[1].value, dict) else el[1].value,
                )
            )
        )

        for mapping in mappings:
            yield mapping
