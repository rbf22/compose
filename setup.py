from distutils.core import setup, Extension

setup(
    name="compose",
    ext_modules=[Extension("compose.parser._tokenizer", ["compose/parser/_tokenizer.c"])],
)
