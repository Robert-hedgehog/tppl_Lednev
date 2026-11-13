import sys
import pytest

from main import Lexer, LexicalError, Token, main


class TestLexer:

    @pytest.mark.parametrize("code", ["", "   ", "\t\n  \r\n"])
    def test_empty_and_whitespace(self, code):
        assert Lexer(code).tokenize() == []

    def test_comments_are_skipped(self):
        source = "# полный комментарий\nx = 1 # комментарий в конце\n# ещё один"
        assert Lexer(source).tokenize() == [
            Token("IDENT", "x", 2, 1),
            Token("OP", "=", 2, 3),
            Token("INT", "1", 2, 5),
        ]

    def test_comment_at_eof_without_newline(self):
        assert Lexer("x = 1 # comment without newline").tokenize() == [
            Token("IDENT", "x", 1, 1),
            Token("OP", "=", 1, 3),
            Token("INT", "1", 1, 5),
        ]

    @pytest.mark.parametrize("kw", ["if", "else", "while", "return", "for", "def"])
    def test_keywords(self, kw):
        assert Lexer(kw).tokenize() == [Token("KEYWORD", kw, 1, 1)]

    @pytest.mark.parametrize("ident", ["x", "_var", "var_123", "for_count", "if1"])
    def test_identifiers(self, ident):
        assert Lexer(ident).tokenize() == [Token("IDENT", ident, 1, 1)]

    @pytest.mark.parametrize(
        "code, expected_type",
        [
            ("0", "INT"),
            ("42", "INT"),
            ("3.14", "FLOAT"),
            (".5", "FLOAT"),
            ("10.", "FLOAT"),
        ],
    )
    def test_numbers(self, code, expected_type):
        assert Lexer(code).tokenize() == [Token(expected_type, code, 1, 1)]

    @pytest.mark.parametrize(
        "code",
        [
            '""',
            '"hello world"',
            r'"escaped \"quote\" and \\ slash # @"',
        ],
    )
    def test_strings(self, code):
        assert Lexer(code).tokenize() == [Token("STRING", code, 1, 1)]

    @pytest.mark.parametrize("op", ["+", "-", "*", "/", "=", "<", ">", "==", "<=", ">="])
    def test_operators(self, op):
        assert Lexer(op).tokenize() == [Token("OP", op, 1, 1)]

    @pytest.mark.parametrize("sep", ["(", ")", "{", "}", ",", ";"])
    def test_separators(self, sep):
        assert Lexer(sep).tokenize() == [Token("SEP", sep, 1, 1)]

    @pytest.mark.parametrize("code", ["x=1", "x = 1", "x =1 ", " x= 1", "\tx = 1\n"])
    def test_spaces_around_tokens(self, code):
        result = [(t.type, t.value) for t in Lexer(code).tokenize()]
        assert result == [("IDENT", "x"), ("OP", "="), ("INT", "1")]

    def test_greedy_two_char_operators(self):
        assert Lexer("a<=10==b>=c").tokenize() == [
            Token("IDENT", "a", 1, 1),
            Token("OP", "<=", 1, 2),
            Token("INT", "10", 1, 4),
            Token("OP", "==", 1, 6),
            Token("IDENT", "b", 1, 8),
            Token("OP", ">=", 1, 9),
            Token("IDENT", "c", 1, 11),
        ]

    def test_multiline_and_crlf_positions(self):
        source = "x = 1\r\n\ty = 2"
        assert Lexer(source).tokenize() == [
            Token("IDENT", "x", 1, 1),
            Token("OP", "=", 1, 3),
            Token("INT", "1", 1, 5),
            Token("IDENT", "y", 2, 2),
            Token("OP", "=", 2, 4),
            Token("INT", "2", 2, 6),
        ]

    def test_example_from_specification(self):
        output = [str(t) for t in Lexer("x = y * 2 + z * 3").tokenize()]
        assert output == [
            "(IDENT, x, 1:1)",
            "(OP, =, 1:3)",
            "(IDENT, y, 1:5)",
            "(OP, *, 1:7)",
            "(INT, 2, 1:9)",
            "(OP, +, 1:11)",
            "(IDENT, z, 1:13)",
            "(OP, *, 1:15)",
            "(INT, 3, 1:17)",
        ]

    @pytest.mark.parametrize(
        "code, bad_char, exp_line, exp_col",
        [
            ("a @ b", "@", 1, 3),
            ("while x > 0:", ":", 1, 12),
            ("x = 1\ny = &", "&", 2, 5),
            (".", ".", 1, 1),
            ("a.b", ".", 1, 2),
        ],
    )
    def test_invalid_characters(self, code, bad_char, exp_line, exp_col):
        with pytest.raises(LexicalError) as exc_info:
            Lexer(code).tokenize()

        assert (exc_info.value.line, exc_info.value.col) == (exp_line, exp_col)
        assert f"unexpected character {bad_char!r}" in str(exc_info.value)

    @pytest.mark.parametrize("code", ['"unclosed', '"line1\nline2"', '"escape\\', r'"abc\"'])
    def test_unterminated_string(self, code):
        with pytest.raises(LexicalError) as exc_info:
            Lexer(code).tokenize()

        assert (exc_info.value.line, exc_info.value.col) == (1, 1)


class TestCLI:

    def test_cli_success(self, tmp_path, monkeypatch, capsys):
        src = tmp_path / "input.txt"
        src.write_text("x = 10;", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["main.py", str(src)])

        main()

        captured = capsys.readouterr()
        assert captured.out.splitlines() == [
            "(IDENT, x, 1:1)",
            "(OP, =, 1:3)",
            "(INT, 10, 1:5)",
            "(SEP, ;, 1:7)",
        ]
        assert captured.err == ""

    def test_cli_lexical_error(self, tmp_path, monkeypatch, capsys):
        src = tmp_path / "input.txt"
        src.write_text("a @ b", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["main.py", str(src)])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.strip() == f"{src}:1:3: lexical: unexpected character '@'"

    def test_cli_missing_file(self, tmp_path, monkeypatch, capsys):
        missing = tmp_path / "no_such_file.txt"
        monkeypatch.setattr(sys, "argv", ["main.py", str(missing)])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        assert f"{missing}:0:0: io:" in capsys.readouterr().err

    def test_cli_missing_arguments(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["main.py"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        assert "Usage:" in capsys.readouterr().err