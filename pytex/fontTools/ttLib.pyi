from typing import Any, MutableMapping, Sequence

class TTFont:
    tables: Sequence[Any]

    def __init__(self, path: str, *args: Any, **kwargs: Any) -> None: ...

    def __getitem__(self, key: str) -> Any: ...

    def getGlyphSet(self) -> MutableMapping[str, Any]: ...
