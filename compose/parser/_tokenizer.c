#include <Python.h>

static PyObject* tokenize(PyObject* self, PyObject* args) {
    const char* text;
    if (!PyArg_ParseTuple(args, "s", &text)) return NULL;

    PyObject* tokens = PyList_New(0);
    const char* p = text;
    const char* start;
    while (*p) {
        if (*p == '#') {
            start = p;
            int level = 0;
            while (*p == '#') { level++; p++; }
            while (*p == ' ') p++;
            const char* text_start = p;
            while (*p && *p != '\n') p++;
            PyObject* tuple = PyTuple_Pack(3, PyUnicode_FromString("HEADING"), PyLong_FromLong(level), PyUnicode_FromStringAndSize(text_start, p - text_start));
            PyList_Append(tokens, tuple);
        } else if (*p == '-' && *(p+1) == ' ') {
            p += 2;
            const char* text_start = p;
            while (*p && *p != '\n') p++;
            PyObject* tuple = PyTuple_Pack(2, PyUnicode_FromString("LIST_ITEM"), PyUnicode_FromStringAndSize(text_start, p - text_start));
            PyList_Append(tokens, tuple);
        } else if (*p == '-' && *(p+1) == '-' && *(p+2) == '-') {
            PyList_Append(tokens, PyUnicode_FromString("HR"));
            p += 3;
            while (*p == '-') p++;
        } else if (*p == '\n') {
            p++;
        } else {
            // paragraph
            start = p;
            while (*p && *p != '\n') p++;
            if (p > start) {
                PyObject* tuple = PyTuple_Pack(2, PyUnicode_FromString("PARAGRAPH"), PyUnicode_FromStringAndSize(start, p - start));
                PyList_Append(tokens, tuple);
            }
        }
    }
    return tokens;
}

static PyMethodDef Methods[] = {
    {"tokenize", tokenize, METH_VARARGS, "Tokenize markdown text."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT, "_tokenizer", NULL, -1, Methods
};

PyMODINIT_FUNC PyInit__tokenizer(void) {
    return PyModule_Create(&moduledef);
}
