import os
import datetime
from copy import deepcopy

from definition import QUERY_DEFINITION, AGGREGATION_DEFINITION


INDENT = "    "
HEADLINE = f"# auto-generated by generate_interface.py on {datetime.date.today()}"
TYPING_IMPORT = "from typing import List, Dict"


def generate_query_interface(file):
    print(HEADLINE, file=file)
    print(TYPING_IMPORT, file=file)

    print(f"\nfrom .interface import QueryInterfaceBase\n\n", file=file)

    print("class QueryInterface(QueryInterfaceBase):\n", file=file)

    for query_name in sorted(QUERY_DEFINITION):
        definition = QUERY_DEFINITION[query_name]

        code = ""

        code += f"def {query_name}(\n"
        code += f"{INDENT}{INDENT}self,\n"
        for param_name, param in definition["parameters"].items():
            param_str = f"{param_name}: {type_str(param)}"
            if not param.get("required"):
                param_str += "=" + repr(param.get("default"))
            code += f"{INDENT}{INDENT}{param_str},\n"
        code += ") -> 'QueryInterface':\n"

        code += f'{INDENT}"""\n'
        code += change_text_indent(definition['doc'], INDENT, max_length=80)
        code += f"\n\n{INDENT}See: {definition['url']}\n"

        for param_name, param in definition["parameters"].items():
            code += f"\n\n{INDENT}:param {param_name}: {type_str(param)}\n"
            code += change_text_indent(param["doc"], INDENT*2, max_length=80)

        code += f"\n\n{INDENT}:returns: new QueryInterface instance\n"
        code += f'{INDENT}"""\n'

        code += f"{INDENT}return self.add_query(\n"
        code += f"{INDENT}{INDENT}\"{query_name}\",\n"
        for param_name, param in definition["parameters"].items():
            code += f"{INDENT}{INDENT}{param_name}={param_name},\n"
        code += f"{INDENT})\n"

        print(change_text_indent(code, INDENT) + "\n", file=file)


def generate_query_class_interface(file):
    print(HEADLINE, file=file)
    print(TYPING_IMPORT, file=file)

    print(f"\nfrom .query import Query, QueryInterface\n\n", file=file)

    for query_name in sorted(QUERY_DEFINITION):
        definition = QUERY_DEFINITION[query_name]
        if "auto_generate" in definition and not definition["auto_generate"]:
            continue

        class_name = "".join(p.title() for p in query_name.split("_"))

        # --- class definition ---

        toplevel_param_name = None

        code = f"class {class_name}(Query):\n\n"
        for param_name, param in definition["parameters"].items():
            if param.get("top_level"):
                toplevel_param_name = param_name

        code += f"{INDENT}name = \"{query_name}\"\n"
        if toplevel_param_name:
            code += f"{INDENT}_top_level_parameter = \"{toplevel_param_name}\"\n"
        code += f"{INDENT}_optional_parameters = {{\n"

        for param_name, param in definition["parameters"].items():
            if not param.get("required"):
                default_value = param.get("default")
                code += f"{INDENT}{INDENT}\"{param_name}\": {repr(default_value)},\n"
        code += f"{INDENT}}}\n"

        # --- init definition ---

        code += f"\n{INDENT}def __init__(\n"
        code += f"{INDENT}{INDENT}{INDENT}self,\n"
        for param_name, param in definition["parameters"].items():
            param_str = f"{param_name}: {type_str(param)}"
            if not param.get("required"):
                param_str += "=" + repr(param.get("default"))
            code += f"{INDENT}{INDENT}{INDENT}{param_str},\n"
        code += f"{INDENT}):\n"

        # --- doc string ---

        code += f'{INDENT}{INDENT}"""\n'
        code += change_text_indent(definition['doc'], INDENT*2, max_length=80)
        code += f"\n\n{INDENT}{INDENT}See: {definition['url']}"

        for param_name, param in definition["parameters"].items():
            code += f"\n{INDENT}{INDENT}:param {param_name}: {type_str(param)}\n"
            code += change_text_indent(param["doc"], INDENT*3, max_length=80) + "\n"

        code += f'{INDENT}{INDENT}"""\n'

        # --- init call ---

        code += f"{INDENT}{INDENT}super().__init__(\n"
        for param_name, param in definition["parameters"].items():
            code += f"{INDENT}{INDENT}{INDENT}{param_name}={param_name},\n"
        code += f"{INDENT}{INDENT})\n"

        print(code + "\n", file=file)


def generate_aggregation_interface(file):
    print(HEADLINE, file=file)
    print(TYPING_IMPORT, file=file)
    print(f"\nfrom .interface import AggregationInterfaceBase\n\n", file=file)

    print("class AggregationInterface(AggregationInterfaceBase):\n", file=file)

    agg_def = repr(AGGREGATION_DEFINITION).replace("<class '", "").replace("'>", "")
    print(f"{INDENT}AGGREGATION_DEFINITION = {agg_def}\n", file=file)

    for agg_name in sorted(AGGREGATION_DEFINITION):
        definition = AGGREGATION_DEFINITION[agg_name]

        agg_type = definition["type"]

        # --- method def ---

        code = ""
        code += f"def {agg_type}_{agg_name}(\n"
        code += f"{INDENT}{INDENT}self,\n"
        code += f"{INDENT}{INDENT}*aggregation_name,\n"
        for param_name, param in definition["parameters"].items():
            # TODO: how to nicely handle subvalues
            param_str = f"{param_name.replace('.', '__')}: {type_str(param)}"
            if not param.get("required"):
                param_str += "=" + repr(param.get("default"))
            code += f"{INDENT}{INDENT}{param_str},\n"
        code += ") -> 'AggregationInterface':\n"

        # --- doc string ---

        code += f'{INDENT}"""\n'
        if definition.get("doc"):
            code += change_text_indent(definition['doc'], INDENT, max_length=80)
        code += f"\n\n{INDENT}See: {definition['url']}\n"

        for param_name, param in definition["parameters"].items():
            code += f"\n\n{INDENT}:param {param_name}: {type_str(param)}\n"
            if param.get("doc"):
                code += change_text_indent(param["doc"], INDENT*2, max_length=80)

        code += f"\n\n{INDENT}:returns: new AggregationInterface instance\n"
        code += f'{INDENT}"""\n'

        # --- call generic function ---

        code += f"{INDENT}return self.{agg_type}(\n"
        code += f"{INDENT}{INDENT}*(aggregation_name + (\"{agg_name}\", )),\n"
        for param_name, param in definition["parameters"].items():
            code += f"{INDENT}{INDENT}{param_name.replace('.', '__')}={param_name.replace('.', '__')},\n"
        code += f"{INDENT})\n"

        print(change_text_indent(code, INDENT) + "\n", file=file)


def type_str(param):
    type = param["type"]
    if isinstance(type, str):
        if '[' in type:
            return type
        return repr(type)
    else:
        return type.__name__


def change_text_indent(text, indent, max_length=None):
    """
    Changes the indentation of a block of text.
    All leading whitespace on each line is stripped up to the
    maximum common length of ws for each line and then 'len' spaces are inserted.
    Also merges multiple new-lines into one
    :param indent: int|str, Number of spaces to have in front
    :param max_length: int|None, Number of maximum columns to occupy or None for unlimited
    :return: str
    """
    if not isinstance(indent, int):
        indent = len(indent)

    lines = text.replace("\t", INDENT).split("\n")
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]

    min_space = -1
    for line in lines:
        for i, k in enumerate(line):
            if not (k == " " or k == "\n"):
                if min_space < 0:
                    min_space = i
                else:
                    min_space = min(min_space, i)
                break

    pre = " " * indent
    text = ""
    was_nl = False
    for line in lines:
        li = line[min_space:]
        if li:
            if not max_length:
                text += pre + li + "\n"
            else:
                text += break_line(pre, li, max_length) + "\n"
            was_nl = False
        else:
            if not was_nl:
                text += "\n"
            was_nl = True

    if text.endswith("\n"):
        text = text[:-1]

    return text


def break_line(pre, line, max_length):
    # print("CHECK[", line, "]")
    text = ""
    add_pre = len(line) - len(line.lstrip())
    line = line[add_pre:]
    pre += " " * add_pre

    while line:
        line_part = line
        new_line = pre + line_part
        need_new_line = False
        while len(new_line) > max_length:
            #print("TOO LONG[", len(new_line), new_line, "]")
            need_new_line = True
            try:
                space_idx = line_part.rindex(" ")
            except ValueError:
                break
            if not space_idx:
                break
            line_part = line_part[:space_idx]
            new_line = pre + line_part

        if text:
            text += "\n"
        text += new_line
        line = line[len(line_part)+1:]

    return text


def generate_file(filename, func):
    with open(filename, "w") as fp:
        func(fp)
    print("written", filename)


if __name__ == "__main__":
    generate_file(
        os.path.join("elastipy", "query", "generated_interface.py"),
        generate_query_interface,
    )

    generate_file(
        os.path.join("elastipy", "query", "generated_classes.py"),
        generate_query_class_interface,
    )

    generate_file(
        os.path.join("elastipy", "aggregation", "generated_interface.py"),
        generate_aggregation_interface,
    )
