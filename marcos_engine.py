"""
MARCOS 7.0
Pipeline: código-fonte -> tokens -> AST -> bytecode -> máquina virtual.
Implementação experimental, sem eval() ou exec() de código do usuário.
"""
from __future__ import annotations

import ast as py_ast
import hashlib
import json
import math
import operator
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------
# 1. Lexer
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class Token:
    kind: str
    value: Any
    line: int
    column: int


class Lexer:
    PATTERNS = [
        ("NUMBER", r"(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?"),
        ("STRING", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
        ("IDENT", r"[A-Za-z_][A-Za-z_0-9]*"),
        ("OP", r"\*\*|==|!=|<=|>=|[+\-*/%=<>.,;:{}()\[\]]"),
        ("NEWLINE", r"\n+"),
        ("SPACE", r"[ \t\r]+"),
        ("COMMENT", r"\#[^\n]*"),
    ]
    MASTER = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in PATTERNS))

    KEYWORDS = {
        "if", "else", "while", "for", "in", "func", "return",
        "class", "try", "except", "raise", "import",
        "true", "false", "none", "and", "or", "not",
    }

    def tokenize(self, source: str) -> list[Token]:
        if len(source) > 100000:
            raise ValueError("código-fonte excede o limite de 100 KB")
        tokens: list[Token] = []
        line, column, pos = 1, 1, 0
        while pos < len(source):
            match = self.MASTER.match(source, pos)
            if not match:
                snippet = source[pos:pos + 12]
                raise SyntaxError(f"Caractere inválido na linha {line}, coluna {column}: {snippet!r}")
            kind = match.lastgroup
            value = match.group()
            if kind == "NEWLINE":
                tokens.append(Token("SEP", ";", line, column))
                line += len(value)
                column = 1
            elif kind in ("SPACE", "COMMENT"):
                if kind == "SPACE":
                    column += len(value)
            elif kind == "NUMBER":
                parsed = float(value) if any(c in value for c in ".eE") else int(value)
                tokens.append(Token(kind, parsed, line, column))
                column += len(value)
            elif kind == "STRING":
                try:
                    parsed = py_ast.literal_eval(value)
                except (ValueError, SyntaxError) as exc:
                    raise SyntaxError(f"Texto inválido na linha {line}") from exc
                tokens.append(Token(kind, parsed, line, column))
                column += len(value)
            elif kind == "IDENT":
                tokens.append(Token("KW" if value in self.KEYWORDS else "IDENT", value, line, column))
                column += len(value)
            else:
                # Pontuação e operadores são representados pelo próprio texto.
                tokens.append(Token(value, value, line, column))
                column += len(value)
            if len(tokens) > 200000:
                raise ValueError("programa excede o limite de 200.000 tokens")
            pos = match.end()

        tokens.append(Token("EOF", None, line, column))
        return tokens


# ---------------------------------------------------------------------
# 2. Parser recursivo: gera AST, sem executar o código
# ---------------------------------------------------------------------
@dataclass
class Node:
    kind: str
    value: Any = None
    children: list[Any] | None = None
    line: int = 0


class Parser:
    BINDING_POWER = {
        "or": 1, "and": 2,
        "==": 3, "!=": 3, "<": 3, "<=": 3, ">": 3, ">=": 3,
        "+": 4, "-": 4,
        "*": 5, "/": 5, "%": 5,
        "**": 6,
    }

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.current()
        if token.kind != "EOF":
            self.pos += 1
        return token

    def check(self, kind: str, value: Any = None) -> bool:
        token = self.current()
        return token.kind == kind and (value is None or token.value == value)

    def match(self, kind: str, value: Any = None) -> bool:
        if self.check(kind, value):
            self.advance()
            return True
        return False

    def expect(self, kind: str, value: Any = None) -> Token:
        if not self.check(kind, value):
            token = self.current()
            expected = value if value is not None else kind
            raise SyntaxError(
                f"Linha {token.line}, coluna {token.column}: esperado {expected!r}, "
                f"encontrado {token.value!r}"
            )
        return self.advance()

    def separators(self):
        while self.match("SEP") or self.match(";"):
            pass

    def parse(self) -> Node:
        statements = self.parse_statements("EOF")
        self.expect("EOF")
        return Node("block", children=statements)

    def parse_statements(self, terminator: str) -> list[Node]:
        result: list[Node] = []
        self.separators()
        while not self.check(terminator) and not self.check("EOF"):
            result.append(self.statement())
            if not self.check(terminator) and not self.check("EOF"):
                if not (self.check("SEP") or self.check(";")):
                    token = self.current()
                    raise SyntaxError(
                        f"Linha {token.line}: instruções precisam ser separadas por nova linha ou ';'"
                    )
            self.separators()
        return result

    def block(self) -> Node:
        self.expect("{")
        body = self.parse_statements("}")
        self.expect("}")
        return Node("block", children=body)

    def statement(self) -> Node:
        token = self.current()

        if self.match("KW", "if"):
            self.expect("(")
            condition = self.expression()
            self.expect(")")
            yes = self.block()
            self.separators()
            no = self.block() if self.match("KW", "else") else Node("block", children=[])
            return Node("if", children=[condition, yes, no], line=token.line)

        if self.match("KW", "while"):
            self.expect("(")
            condition = self.expression()
            self.expect(")")
            return Node("while", children=[condition, self.block()], line=token.line)

        if self.match("KW", "for"):
            name = self.expect("IDENT").value
            self.expect("KW", "in")
            iterable = self.expression()
            return Node("for", name, [iterable, self.block()], token.line)

        if self.match("KW", "func"):
            name = self.expect("IDENT").value
            params = self.parameters()
            return Node("func", name, [params, self.block()], token.line)

        if self.match("KW", "class"):
            name = self.expect("IDENT").value
            parent = None
            if self.match("("):
                parent = self.expect("IDENT").value
                self.expect(")")
            body = self.block()
            for child in body.children or []:
                if child.kind != "func":
                    raise SyntaxError(f"Linha {child.line}: classes aceitam declarações func nesta versão")
            return Node("class", name, [parent, body], token.line)

        if self.match("KW", "return"):
            return Node("return", children=[self.expression()], line=token.line)

        if self.match("KW", "try"):
            try_block = self.block()
            self.separators()
            self.expect("KW", "except")
            # except pode capturar todas as exceções; nome do erro é opcional.
            error_name = None
            if self.match("("):
                error_name = self.expect("IDENT").value
                self.expect(")")
            except_block = self.block()
            return Node("try", error_name, [try_block, except_block], token.line)

        if self.match("KW", "raise"):
            return Node("raise", children=[self.expression()], line=token.line)

        if self.match("KW", "import"):
            module = self.expect("IDENT").value
            return Node("import", module, line=token.line)

        left = self.expression()
        if self.match("="):
            if left.kind not in ("name", "attribute", "index"):
                raise SyntaxError(f"Linha {token.line}: destino inválido de atribuição")
            value = self.expression()
            return Node("assign", children=[left, value], line=token.line)
        return Node("expression_statement", children=[left], line=token.line)

    def parameters(self) -> list[str]:
        self.expect("(")
        params = []
        if not self.check(")"):
            params.append(self.expect("IDENT").value)
            while self.match(","):
                params.append(self.expect("IDENT").value)
        self.expect(")")
        if len(params) != len(set(params)):
            raise SyntaxError("parâmetros duplicados não são permitidos")
        return params

    def expression(self, min_bp: int = 0) -> Node:
        token = self.advance()

        if token.kind == "NUMBER" or token.kind == "STRING":
            left = Node("literal", token.value, line=token.line)
        elif token.kind == "IDENT":
            left = Node("name", token.value, line=token.line)
        elif token.kind == "KW" and token.value in ("true", "false", "none"):
            value = {"true": True, "false": False, "none": None}[token.value]
            left = Node("literal", value, line=token.line)
        elif token.kind == "KW" and token.value == "not":
            left = Node("unary", "not", [self.expression(7)], token.line)
        elif token.kind == "-":
            left = Node("unary", "-", [self.expression(7)], token.line)
        elif token.kind == "(":
            left = self.expression()
            self.expect(")")
        elif token.kind == "[":
            values = self.expression_list("]")
            left = Node("list", children=values, line=token.line)
        elif token.kind == "{":
            entries = []
            if not self.check("}"):
                while True:
                    key = self.expression()
                    self.expect(":")
                    value = self.expression()
                    entries.append((key, value))
                    if not self.match(","):
                        break
            self.expect("}")
            left = Node("dict", children=entries, line=token.line)
        else:
            raise SyntaxError(f"Linha {token.line}: expressão inesperada {token.value!r}")

        while True:
            # Postfixes: function call, attribute and indexing.
            if self.check("(") and 8 >= min_bp:
                self.advance()
                args = self.expression_list(")")
                left = Node("call", children=[left, *args], line=token.line)
                continue
            if self.match(".") and 8 >= min_bp:
                attr = self.expect("IDENT").value
                left = Node("attribute", attr, [left], token.line)
                continue
            if self.match("[") and 8 >= min_bp:
                index = self.expression()
                self.expect("]")
                left = Node("index", children=[left, index], line=token.line)
                continue

            op_token = self.current()
            op = op_token.value
            bp = self.BINDING_POWER.get(op)
            if bp is None or bp < min_bp:
                break
            self.advance()
            # ** is right associative.
            right = self.expression(bp if op == "**" else bp + 1)
            left = Node("binary", op, [left, right], op_token.line)
        return left

    def expression_list(self, terminator: str) -> list[Node]:
        values = []
        if not self.check(terminator):
            values.append(self.expression())
            while self.match(","):
                values.append(self.expression())
        self.expect(terminator)
        return values


# ---------------------------------------------------------------------
# 3. Bytecode / representação intermediária
# ---------------------------------------------------------------------
@dataclass
class Instruction:
    op: str
    arg: Any = None
    line: int = 0


@dataclass
class CodeObject:
    name: str
    instructions: list[Instruction]
    params: list[str] | None = None


class Compiler:
    def compile(self, tree: Node, name: str = "<main>") -> CodeObject:
        self.code: list[Instruction] = []
        self.name = name
        for statement in tree.children or []:
            self.statement(statement)
        self.emit("PUSH_CONST", None)
        self.emit("RETURN")
        return CodeObject(name, self.code)

    def emit(self, op: str, arg: Any = None, line: int = 0) -> int:
        self.code.append(Instruction(op, arg, line))
        return len(self.code) - 1

    def patch(self, index: int, target: int):
        self.code[index].arg = target

    def compile_nested(self, node: Node, name: str, params=None) -> CodeObject:
        nested = Compiler()
        result = nested.compile(node, name)
        result.params = params or []
        return result

    def statement(self, node: Node):
        kind = node.kind
        if kind == "assign":
            target, value = node.children
            self.expression(value)
            if target.kind == "name":
                self.emit("STORE_NAME", target.value, node.line)
            elif target.kind == "attribute":
                self.expression(target.children[0])
                # Stack order adjusted by SET_ATTR: object, value.
                self.emit("SWAP")
                self.emit("SET_ATTR", target.value, node.line)
            elif target.kind == "index":
                self.expression(target.children[0])
                self.expression(target.children[1])
                self.emit("ROT3")
                self.emit("SET_ITEM", line=node.line)
        elif kind == "expression_statement":
            self.expression(node.children[0])
            self.emit("POP")
        elif kind == "if":
            condition, yes, no = node.children
            self.expression(condition)
            branch = self.emit("JUMP_IF_FALSE", None, node.line)
            self.block(yes)
            end_jump = self.emit("JUMP")
            self.patch(branch, len(self.code))
            self.block(no)
            self.patch(end_jump, len(self.code))
        elif kind == "while":
            condition, body = node.children
            start = len(self.code)
            self.expression(condition)
            exit_jump = self.emit("JUMP_IF_FALSE", None, node.line)
            self.block(body)
            self.emit("JUMP", start)
            self.patch(exit_jump, len(self.code))
        elif kind == "for":
            iterable, body = node.children
            self.expression(iterable)
            self.emit("GET_ITER")
            next_index = self.emit("FOR_NEXT", (node.value, None), node.line)
            self.block(body)
            self.emit("JUMP", next_index)
            self.code[next_index].arg = (node.value, len(self.code))
        elif kind == "func":
            params, body = node.children
            function_code = self.compile_nested(body, node.value, params)
            self.emit("MAKE_FUNCTION", (node.value, function_code), node.line)
        elif kind == "class":
            parent, body = node.children
            method_specs = {}
            for method in body.children or []:
                params, method_body = method.children
                method_specs[method.value] = self.compile_nested(
                    method_body, f"{node.value}.{method.value}", params
                )
            self.emit("MAKE_CLASS", (node.value, parent, method_specs), node.line)
        elif kind == "return":
            self.expression(node.children[0])
            self.emit("RETURN", line=node.line)
        elif kind == "try":
            try_body, except_body = node.children
            handler = self.emit("TRY_BEGIN", None, node.line)
            self.block(try_body)
            self.emit("TRY_END")
            skip = self.emit("JUMP")
            self.patch(handler, len(self.code))
            self.emit("STORE_EXCEPTION", node.value or "error")
            self.block(except_body)
            self.patch(skip, len(self.code))
        elif kind == "raise":
            self.expression(node.children[0])
            self.emit("RAISE", line=node.line)
        elif kind == "import":
            self.emit("IMPORT", node.value, node.line)
        else:
            raise SyntaxError(f"Linha {node.line}: instrução não compilável: {kind}")

    def block(self, node: Node):
        for item in node.children or []:
            self.statement(item)

    def expression(self, node: Node):
        kind = node.kind
        if kind == "literal":
            self.emit("PUSH_CONST", node.value, node.line)
        elif kind == "name":
            self.emit("LOAD_NAME", node.value, node.line)
        elif kind == "list":
            for value in node.children or []:
                self.expression(value)
            self.emit("BUILD_LIST", len(node.children or []), node.line)
        elif kind == "dict":
            for key, value in node.children or []:
                self.expression(key)
                self.expression(value)
            self.emit("BUILD_DICT", len(node.children or []), node.line)
        elif kind == "unary":
            self.expression(node.children[0])
            self.emit("UNARY", node.value, node.line)
        elif kind == "binary":
            self.expression(node.children[0])
            self.expression(node.children[1])
            self.emit("BINARY", node.value, node.line)
        elif kind == "call":
            callee, *args = node.children
            self.expression(callee)
            for arg in args:
                self.expression(arg)
            self.emit("CALL", len(args), node.line)
        elif kind == "attribute":
            self.expression(node.children[0])
            self.emit("GET_ATTR", node.value, node.line)
        elif kind == "index":
            self.expression(node.children[0])
            self.expression(node.children[1])
            self.emit("GET_ITEM", line=node.line)
        else:
            raise SyntaxError(f"Linha {node.line}: expressão não compilável: {kind}")


# ---------------------------------------------------------------------
# 4. Máquina virtual
# ---------------------------------------------------------------------
@dataclass
class UserFunction:
    code: CodeObject


@dataclass
class BoundMethod:
    instance: "MarcosObject"
    function: UserFunction


@dataclass
class MarcosClass:
    name: str
    parent: "MarcosClass | None"
    methods: dict[str, UserFunction]


@dataclass
class MarcosObject:
    klass: MarcosClass
    fields: dict[str, Any]


@dataclass
class SafeModule:
    name: str
    exports: dict[str, Any]


class MarcosVM:
    BINARY = {
        "+": operator.add, "-": operator.sub, "*": operator.mul,
        "/": operator.truediv, "%": operator.mod, "**": operator.pow,
        "==": operator.eq, "!=": operator.ne,
        "<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge,
        "and": lambda a, b: bool(a) and bool(b),
        "or": lambda a, b: bool(a) or bool(b),
    }

    def __init__(self):
        self.globals: dict[str, Any] = {}
        self.output: list[str] = []
        self.loop_limit = 10000
        self.call_depth = 0
        self.max_call_depth = 100
        self.max_instructions = 250000
        self.instruction_count = 0
        self.debug_enabled = False
        self.trace: list[dict[str, Any]] = []
        self.last_code: CodeObject | None = None

    def builtins(self):
        def safe_range(*args):
            values = range(*args)
            if len(values) > 100000:
                raise ValueError("range excede o limite de 100.000 elementos")
            return list(values)

        def safe_factorial(value):
            if not isinstance(value, int) or value < 0 or value > 1000:
                raise ValueError("factorial aceita inteiros entre 0 e 1000")
            return math.factorial(value)

        return {
            "len": len, "abs": abs, "round": round,
            "min": min, "max": max, "sum": sum,
            "range": safe_range,
            "str": str, "int": int, "float": float,
        }

    def load_name(self, name, local):
        if name in local:
            return local[name]
        if name in self.globals:
            return self.globals[name]
        if name in self.builtins():
            return self.builtins()[name]
        raise NameError(f"nome '{name}' não definido")

    def find_method(self, klass: MarcosClass, name: str):
        current = klass
        while current:
            if name in current.methods:
                return current.methods[name]
            current = current.parent
        raise AttributeError(f"método '{name}' não encontrado em {klass.name}")

    def get_attr(self, obj, name):
        if isinstance(obj, MarcosObject):
            if name in obj.fields:
                # Convenção de privacidade: atributos com _ são internos.
                return obj.fields[name]
            return BoundMethod(obj, self.find_method(obj.klass, name))
        if isinstance(obj, SafeModule) and name in obj.exports:
            return obj.exports[name]
        raise AttributeError(f"atributo '{name}' não disponível")

    def call(self, callable_value, args):
        if isinstance(callable_value, BoundMethod):
            return self.call_function(callable_value.function, [callable_value.instance, *args])
        if isinstance(callable_value, UserFunction):
            return self.call_function(callable_value, args)
        if isinstance(callable_value, MarcosClass):
            instance = MarcosObject(callable_value, {})
            try:
                initializer = self.find_method(callable_value, "init")
                self.call_function(initializer, [instance, *args])
            except AttributeError:
                if args:
                    raise TypeError(f"{callable_value.name} não aceita argumentos")
            return instance
        if callable(callable_value):
            return callable_value(*args)
        raise TypeError("este valor não pode ser chamado")

    def call_function(self, function: UserFunction, args):
        params = function.code.params or []
        if len(params) != len(args):
            raise TypeError(
                f"{function.code.name} espera {len(params)} argumento(s), recebeu {len(args)}"
            )
        self.call_depth += 1
        if self.call_depth > self.max_call_depth:
            self.call_depth -= 1
            raise RecursionError("profundidade máxima de chamadas excedida")
        local = dict(zip(params, args))
        try:
            return self.run_code(function.code, local, is_function=True)
        finally:
            self.call_depth -= 1

    def run_code(self, code: CodeObject, local=None, is_function=False):
        local = {} if local is None else local
        stack: list[Any] = []
        handlers: list[tuple[int, int]] = []
        iterators: list[Any] = []
        ip = 0
        instructions = code.instructions

        while ip < len(instructions):
            ins = instructions[ip]
            op, arg = ins.op, ins.arg
            self.instruction_count += 1
            if self.instruction_count > self.max_instructions:
                raise RuntimeError("limite de instruções excedido")
            if self.debug_enabled and len(self.trace) < 30000:
                self.trace.append({
                    "index": len(self.trace),
                    "function": code.name,
                    "ip": ip,
                    "op": op,
                    "arg": self._debug_repr(arg),
                    "line": ins.line,
                    "stack": [self._debug_repr(item) for item in stack[-12:]],
                    "locals": {k: self._debug_repr(v) for k, v in list(local.items())[:30]},
                })
            try:
                if op == "PUSH_CONST":
                    stack.append(arg)
                elif op == "LOAD_NAME":
                    stack.append(self.load_name(arg, local))
                elif op == "STORE_NAME":
                    value = stack.pop()
                    (local if is_function else self.globals)[arg] = value
                elif op == "POP":
                    stack.pop()
                elif op == "SWAP":
                    a, b = stack.pop(), stack.pop()
                    stack.extend([a, b])
                elif op == "ROT3":
                    # A pilha recebe [valor, objeto, índice]; reorganiza para
                    # [objeto, índice, valor], a ordem esperada por SET_ITEM.
                    index = stack.pop()
                    obj = stack.pop()
                    value = stack.pop()
                    stack.extend([obj, index, value])
                elif op == "BUILD_LIST":
                    values = stack[-arg:] if arg else []
                    if arg:
                        del stack[-arg:]
                    stack.append(list(values))
                elif op == "BUILD_DICT":
                    count = arg
                    values = stack[-2 * count:] if count else []
                    if count:
                        del stack[-2 * count:]
                    result = {}
                    for i in range(0, len(values), 2):
                        result[values[i]] = values[i + 1]
                    stack.append(result)
                elif op == "UNARY":
                    value = stack.pop()
                    stack.append(-value if arg == "-" else not value)
                elif op == "BINARY":
                    right, left = stack.pop(), stack.pop()
                    if arg in ("/", "%") and right == 0:
                        raise ZeroDivisionError("divisão ou módulo por zero")
                    if arg == "**" and abs(right) > 1000:
                        raise ValueError("expoente excede o limite de 1000")
                    if arg == "+" and (isinstance(left, str) or isinstance(right, str)):
                        value = str(left) + str(right)
                    else:
                        value = self.BINARY[arg](left, right)
                    if isinstance(value, complex):
                        raise ValueError("resultados complexos não são suportados")
                    if isinstance(value, (int, float)) and abs(value) > 1e100:
                        raise ValueError("resultado numérico excede o limite")
                    stack.append(value)
                elif op == "CALL":
                    args = stack[-arg:] if arg else []
                    if arg:
                        del stack[-arg:]
                    fn = stack.pop()
                    stack.append(self.call(fn, args))
                elif op == "GET_ATTR":
                    stack.append(self.get_attr(stack.pop(), arg))
                elif op == "GET_ITEM":
                    index, obj = stack.pop(), stack.pop()
                    stack.append(obj[index])
                elif op == "SET_ATTR":
                    value, obj = stack.pop(), stack.pop()
                    if not isinstance(obj, MarcosObject):
                        raise TypeError("atributo só pode ser definido em objeto MARCOS")
                    obj.fields[arg] = value
                elif op == "SET_ITEM":
                    value, index, obj = stack.pop(), stack.pop(), stack.pop()
                    obj[index] = value
                elif op == "JUMP":
                    ip = arg
                    continue
                elif op == "JUMP_IF_FALSE":
                    if not stack.pop():
                        ip = arg
                        continue
                elif op == "GET_ITER":
                    iterators.append(iter(stack.pop()))
                elif op == "FOR_NEXT":
                    try:
                        value = next(iterators[-1])
                        (local if is_function else self.globals)[arg[0]] = value
                    except StopIteration:
                        iterators.pop()
                        ip = arg[1]
                        continue
                elif op == "MAKE_FUNCTION":
                    name, fn_code = arg
                    self.globals[name] = UserFunction(fn_code)
                elif op == "MAKE_CLASS":
                    name, parent_name, methods = arg
                    parent = None
                    if parent_name:
                        parent = self.load_name(parent_name, local)
                        if not isinstance(parent, MarcosClass):
                            raise TypeError(f"{parent_name} não é uma classe")
                    built_methods = {k: UserFunction(v) for k, v in methods.items()}
                    self.globals[name] = MarcosClass(name, parent, built_methods)
                elif op == "IMPORT":
                    modules = {
                        "math": {
                            "pi": math.pi, "e": math.e, "tau": math.tau,
                            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                            "tan": math.tan, "floor": math.floor, "ceil": math.ceil,
                            "factorial": math.factorial,
                        },
                        "text": {
                            "upper": lambda value: str(value).upper(),
                            "lower": lambda value: str(value).lower(),
                            "trim": lambda value: str(value).strip(),
                            "replace": lambda value, old, new: str(value).replace(old, new),
                        },
                        "stats": {
                            "mean": lambda values: sum(values) / len(values),
                            "minimum": min,
                            "maximum": max,
                        },
                    }
                    if arg not in modules:
                        raise ImportError(f"módulo '{arg}' não está na biblioteca padrão permitida")
                    self.globals[arg] = SafeModule(arg, modules[arg])
                elif op == "TRY_BEGIN":
                    handlers.append((arg, len(stack)))
                elif op == "TRY_END":
                    if handlers:
                        handlers.pop()
                elif op == "STORE_EXCEPTION":
                    message = stack.pop() if stack else "erro"
                    (local if is_function else self.globals)[arg] = message
                elif op == "RAISE":
                    raise RuntimeError(str(stack.pop()))
                elif op == "RETURN":
                    return stack.pop() if stack else None
                else:
                    raise RuntimeError(f"opcode desconhecido: {op}")
                ip += 1
            except Exception as exc:
                if handlers:
                    target, stack_size = handlers.pop()
                    del stack[stack_size:]
                    stack.append(f"{type(exc).__name__}: {exc}")
                    ip = target
                else:
                    if ins.line:
                        raise RuntimeError(
                            f"Linha {ins.line}: {type(exc).__name__}: {exc}"
                        ) from exc
                    raise
        return None

    @staticmethod
    def _debug_repr(value):
        if isinstance(value, (str, int, float, bool)) or value is None:
            return repr(value)
        if isinstance(value, MarcosObject):
            return f"<objeto {value.klass.name}>"
        if isinstance(value, MarcosClass):
            return f"<classe {value.name}>"
        if isinstance(value, UserFunction):
            return f"<função {value.code.name}>"
        if isinstance(value, SafeModule):
            return f"<módulo {value.name}>"
        rendered = repr(value)
        return rendered[:180]

    def execute(self, code: CodeObject, debug: bool = False):
        self.output = []
        self.last_code = code
        self.instruction_count = 0
        self.debug_enabled = debug
        self.trace = []
        # Capture print through a safe builtin injected only for this run.
        original = self.builtins
        builtins_map = original()

        def language_print(*values):
            self.output.append(" ".join(str(v) for v in values))
            return None

        builtins_map["print"] = language_print
        # Temporarily provide language built-ins in the global namespace.
        old_print = self.globals.get("print", None)
        had_print = "print" in self.globals
        self.globals["print"] = language_print
        try:
            self.run_code(code)
        finally:
            if had_print:
                self.globals["print"] = old_print
            else:
                self.globals.pop("print", None)
        return self.output

    def snapshot(self):
        result = {}
        for name, value in sorted(self.globals.items()):
            if name == "print":
                continue
            if isinstance(value, MarcosObject):
                result[name] = f"<objeto {value.klass.name}>"
            elif isinstance(value, MarcosClass):
                result[name] = f"<classe {value.name}>"
            elif isinstance(value, UserFunction):
                result[name] = f"<função {value.code.name}>"
            else:
                result[name] = repr(value)
        return result


# ---------------------------------------------------------------------
# 5. Compilação, formato .marc e runtime
# ---------------------------------------------------------------------
MARCOS_MAGIC = "MARCOS_BYTECODE"
MARCOS_FORMAT_VERSION = 1
MARCOS_LANGUAGE_VERSION = "6.0.0"
ALLOWED_OPCODES = {
    "PUSH_CONST", "LOAD_NAME", "STORE_NAME", "POP", "SWAP", "ROT3",
    "BUILD_LIST", "BUILD_DICT", "UNARY", "BINARY", "CALL", "GET_ATTR",
    "GET_ITEM", "SET_ATTR", "SET_ITEM", "JUMP", "JUMP_IF_FALSE",
    "GET_ITER", "FOR_NEXT", "MAKE_FUNCTION", "MAKE_CLASS", "IMPORT",
    "TRY_BEGIN", "TRY_END", "STORE_EXCEPTION", "RAISE", "RETURN",
}


def _encode_value(value):
    if isinstance(value, CodeObject):
        return {
            "__type__": "CodeObject",
            "name": value.name,
            "params": value.params,
            "instructions": [
                {"op": item.op, "arg": _encode_value(item.arg), "line": item.line}
                for item in value.instructions
            ],
        }
    if isinstance(value, tuple):
        return {"__type__": "tuple", "items": [_encode_value(x) for x in value]}
    if isinstance(value, list):
        return {"__type__": "list", "items": [_encode_value(x) for x in value]}
    if isinstance(value, dict):
        return {
            "__type__": "dict",
            "items": [[_encode_value(k), _encode_value(v)] for k, v in value.items()],
        }
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"valor não serializável no bytecode: {type(value).__name__}")


def _decode_value(value, depth=0):
    if depth > 80:
        raise ValueError("bytecode excede a profundidade permitida")
    if not isinstance(value, dict) or "__type__" not in value:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise ValueError("valor inválido no arquivo MARC")
    kind = value.get("__type__")
    if kind == "tuple":
        return tuple(_decode_value(x, depth + 1) for x in value.get("items", []))
    if kind == "list":
        return [_decode_value(x, depth + 1) for x in value.get("items", [])]
    if kind == "dict":
        return {
            _decode_value(k, depth + 1): _decode_value(v, depth + 1)
            for k, v in value.get("items", [])
        }
    if kind == "CodeObject":
        instructions = []
        raw = value.get("instructions")
        if not isinstance(raw, list) or len(raw) > 250000:
            raise ValueError("lista de instruções inválida")
        for item in raw:
            op = item.get("op")
            if op not in ALLOWED_OPCODES:
                raise ValueError(f"opcode não permitido: {op!r}")
            instructions.append(Instruction(
                op=op,
                arg=_decode_value(item.get("arg"), depth + 1),
                line=int(item.get("line", 0)),
            ))
        params = value.get("params")
        if params is not None and not isinstance(params, list):
            raise ValueError("parâmetros inválidos")
        return CodeObject(str(value.get("name", "<carregado>")), instructions, params)
    raise ValueError(f"tipo serializado não permitido: {kind!r}")


def save_bytecode(code: CodeObject, path: str | Path):
    payload = _encode_value(code)
    payload_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    document = {
        "magic": MARCOS_MAGIC,
        "format_version": MARCOS_FORMAT_VERSION,
        "language_version": MARCOS_LANGUAGE_VERSION,
        "sha256": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        "payload": payload,
    }
    Path(path).write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_bytecode(path: str | Path) -> CodeObject:
    file_path = Path(path)
    if file_path.stat().st_size > 5_000_000:
        raise ValueError("arquivo MARC excede 5 MB")
    document = json.loads(file_path.read_text(encoding="utf-8"))
    if document.get("magic") != MARCOS_MAGIC:
        raise ValueError("arquivo não é um bytecode MARCOS")
    if document.get("format_version") != MARCOS_FORMAT_VERSION:
        raise ValueError("versão de formato MARC não suportada")
    payload_text = json.dumps(
        document.get("payload"), ensure_ascii=False, separators=(",", ":")
    )
    checksum = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    if checksum != document.get("sha256"):
        raise ValueError("integridade do bytecode inválida (SHA-256 divergente)")
    decoded = _decode_value(document["payload"])
    if not isinstance(decoded, CodeObject):
        raise ValueError("o payload do arquivo não contém um programa compilado")
    return decoded


class MarcosCompiler:
    def compile_source(self, source: str, name: str = "<main>") -> CodeObject:
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        tree = Parser(tokens).parse()
        compiler = Compiler()
        return compiler.compile(tree, name=name)

    @staticmethod
    def disassemble(code: CodeObject) -> str:
        lines = [f"BYTECODE MARCOS 6.0 — {code.name}"]
        for index, ins in enumerate(code.instructions):
            arg = ins.arg
            if isinstance(arg, CodeObject):
                arg = f"<CodeObject {arg.name}>"
            elif isinstance(arg, tuple) and len(arg) > 2 and isinstance(arg[-1], dict):
                arg = (arg[0], arg[1], f"<{len(arg[2])} métodos>")
            lines.append(f"{index:04d}  linha {ins.line:<4} {ins.op:<18} {arg!r}")
        return "\n".join(lines)


class MarcosRuntime:
    def __init__(self):
        self.compiler = MarcosCompiler()
        self.vm = MarcosVM()
        self.last_bytecode = ""
        self.last_code: CodeObject | None = None

    def compile(self, source: str, name: str = "<main>") -> CodeObject:
        code = self.compiler.compile_source(source, name)
        self.last_code = code
        self.last_bytecode = self.compiler.disassemble(code)
        return code

    def run(self, source: str, debug: bool = False):
        code = self.compile(source)
        return self.vm.execute(code, debug=debug)

    def run_compiled(self, code: CodeObject, debug: bool = False):
        self.last_code = code
        self.last_bytecode = self.compiler.disassemble(code)
        return self.vm.execute(code, debug=debug)

    def save(self, source: str, path: str | Path):
        code = self.compile(source, name=Path(path).name)
        save_bytecode(code, path)
        return code

    def run_file(self, path: str | Path, debug: bool = False):
        code = load_bytecode(path)
        return self.run_compiled(code, debug=debug)
