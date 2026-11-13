import sys

KEYWORDS = {"if", "else", "while", "return", "for", "def"}
SINGLE_OPERATORS = {"+", "-", "*", "/", "=", "<", ">"}
TWO_CHAR_OPERATORS = {"==", "<=", ">="}
SEPARATORS = {"(", ")", "{", "}", ",", ";"}


class Token:
    def __init__(self, type: str, value: str, line: int, col: int):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return (self.type, self.value, self.line, self.col) == (
            other.type, other.value, other.line, other.col
        )

    def __str__(self):
        return f"({self.type}, {self.value}, {self.line}:{self.col})"

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, {self.line}, {self.col})"


class LexicalError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(message)
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.ch = text[0] if text else None

    def advance(self):
        if self.ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1
        self.ch = self.text[self.pos] if self.pos < len(self.text) else None

    def skip(self):
        while self.ch is not None:
            if self.ch.isspace():
                self.advance()
            elif self.ch == "#":
                while self.ch not in (None, "\n"):
                    self.advance()
            else:
                break

    def identifier(self):
        start, line, col = self.pos, self.line, self.col
        while self.ch is not None and (self.ch.isalnum() or self.ch == "_"):
            self.advance()
        lexeme = self.text[start:self.pos]
        kind = "KEYWORD" if lexeme in KEYWORDS else "IDENT"
        return Token(kind, lexeme, line, col)

    def number(self):
        start, line, col = self.pos, self.line, self.col
        digits = 0
        is_float = False

        while self.ch is not None and "0" <= self.ch <= "9":
            digits += 1
            self.advance()

        if self.ch == ".":
            is_float = True
            self.advance()
            while self.ch is not None and "0" <= self.ch <= "9":
                digits += 1
                self.advance()

        if digits == 0:
            raise LexicalError("unexpected character '.'", line, col)

        kind = "FLOAT" if is_float else "INT"
        return Token(kind, self.text[start:self.pos], line, col)

    def string(self):
        start, line, col = self.pos, self.line, self.col
        self.advance()

        while self.ch not in (None, '"'):
            if self.ch == "\n":
                raise LexicalError("unterminated string literal", line, col)
            if self.ch == "\\":
                self.advance()
                if self.ch in (None, "\n"):
                    raise LexicalError("unterminated string literal", line, col)
            self.advance()

        if self.ch != '"':
            raise LexicalError("unterminated string literal", line, col)

        self.advance()
        return Token("STRING", self.text[start:self.pos], line, col)

    def next(self):
        self.skip()
        if self.ch is None:
            return None

        line, col, ch = self.line, self.col, self.ch
        if ch.isalpha() or ch == "_":
            return self.identifier()
        if ("0" <= ch <= "9") or ch == ".":
            return self.number()
        if ch == '"':
            return self.string()

        nxt = self.text[self.pos + 1] if self.pos + 1 < len(self.text) else ""
        if ch + nxt in TWO_CHAR_OPERATORS:
            self.advance()
            self.advance()
            return Token("OP", ch + nxt, line, col)
        if ch in SINGLE_OPERATORS:
            self.advance()
            return Token("OP", ch, line, col)
        if ch in SEPARATORS:
            self.advance()
            return Token("SEP", ch, line, col)

        raise LexicalError(f"unexpected character {ch!r}", line, col)

    def tokenize(self):
        tokens = []
        while True:
            tok = self.next()
            if tok is None:
                break
            tokens.append(tok)
        return tokens


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <source_file>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            source = file.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"{filepath}:0:0: io: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        for token in Lexer(source).tokenize():
            print(token)
    except LexicalError as err:
        print(f"{filepath}:{err.line}:{err.col}: lexical: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()