import re
import types

from html5tagger import E
from niceback.logging import logger

blacklist_names = {"_", "In", "Out"}
blacklist_types = (
    types.ModuleType,
    types.FunctionType,
    types.MethodType,
    types.BuiltinFunctionType,
)
no_str_conv = re.compile(r"<.* object at 0x[0-9a-f]{5,}>")


def extract_variables(variables, sourcecode):
    identifiers = {
        m.group(0)
        for p in (r'\w+', r'\w+\.\w+')
        for m in re.finditer(p, sourcecode)
    }
    rows = []
    for name, value in variables.items():
        if name in blacklist_names or isinstance(value, blacklist_types):
            continue
        try:
            typename = type(value).__name__
            if name not in identifiers:
                continue
            # Try to print members of objects that don't have proper __str__
            if no_str_conv.fullmatch(str(value)):
                found = False
                for n, v in vars(value).items():
                    mname = f'{name}.{n}'
                    if sourcecode and mname not in identifiers:
                        continue
                    tname = type(v).__name__
                    if tname in blacklist_types:
                        continue
                    tname += f' in {typename}'
                    rows += (mname, tname, prettyvalue(v)),
                    found = True
                if found:
                    continue
                value = ''
            # Append dtype on Numpy-style arrays (but not on np.float64 etc)
            if hasattr(value, 'dtype') and hasattr(value, "__iter__"):
                typename += f' of {value.dtype}'
            rows += (name, typename, prettyvalue(value)),
        except Exception:
            logger.exception("Variable inspector failed (please report a bug)")
    return rows


def prettyvalue(val):
    if isinstance(val, (list, tuple)):
        if len(val) > 10:
            return f'({len(val)} items)'
        return E(", ".join(repr(v)[:80] for v in val))
    try:
        # This only works for Numpy-like arrays, and should cause exceptions otherwise
        if val.size > 100:
            return E(f'({"×".join(str(d) for d in val.shape)})')
        elif len(val.shape) == 2:
            with E.table as doc:
                for row in val:
                    doc.tr
                    for num in row:
                        doc.td(f'{num:.2g}' if isinstance(num, float) else num)
            return doc
    except AttributeError:
        pass
    except Exception:
        logger.exception("Pretty-printing in variable inspector failed (please report a bug)")
    ret = f"{val}"
    if len(ret) > 80:
        return E(ret[:30] + " … " + ret[-30:])
    return E(ret)