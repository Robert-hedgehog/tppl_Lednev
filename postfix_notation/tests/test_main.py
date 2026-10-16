from pathlib import Path
import runpy
import sys
import pytest
from main import (
    pf_add,
    pf_sub,
    pf_mul,
    pf_div,
    pf_tilde,
    evaluate,
    main,
)


class TestOperations:
    @pytest.mark.parametrize(
        "func, x, y, expected",
        [
            (pf_add, 10, 5, 15),
            (pf_add, -4, 6, 2),
            (pf_sub, 20, 7, 13),
            (pf_sub, 3, 10, -7),
            (pf_mul, 6, 7, 42),
            (pf_mul, -2, 5, -10),
            (pf_div, 12, 3, 4),
            (pf_div, 9, 2, 4.5),
        ],
    )
    def test_standard_math(self, func, x, y, expected):
        assert func(x, y) == expected

    def test_zero_division_safety(self):
        assert pf_div(15, 0) is None

    @pytest.mark.parametrize(
        "x, y, stack_state, expected",
        [
            (8, 3, [], 5),
            (3, 8, [], 5),
            (6, 6, [], 0),
            (0, 4, [3], 49),
            (0, 4, [], 16),
            (0, 0, [2, 3], 25),
        ],
    )
    def test_tilde_math(self, x, y, stack_state, expected):
        assert pf_tilde(x, y, stack=stack_state) == expected


class TestCalculation:
    @pytest.mark.parametrize(
        "expression, expected",
        [
            ("3 0 4 ~ 2 ~", 47),
            ("2 2 + 4 - 4 ~ 2 3 * +", 22),
            ("10 4 - 2 *", 12),
            ("16 4 / 2 /", 2),
            ("9 2 /", 4.5),
            ("50", 50),
        ],
    )
    def test_valid_runs(self, expression, expected):
        assert evaluate(expression) == expected

    @pytest.mark.parametrize(
        "bad_expression",
        [
            "",
            "   ",
            "+",
            "~",
            "5 +",
            "10 0 /",
            "4 2 bad_word +",
            "1 2 3 +",
        ],
    )
    def test_error_handling(self, bad_expression):
        assert evaluate(bad_expression) is None


class TestStepLogging:
    def test_console_steps_output(self, capsys):
        res = evaluate("4 5 +")
        assert res == 9

        captured = capsys.readouterr().out
        assert "Шаг 1: число 4 -> стек: [4]" in captured
        assert "Шаг 2: число 5 -> стек: [4, 5]" in captured
        assert "Шаг 3: '+' -> стек: [9]" in captured


class TestTerminalInterface:
    @pytest.mark.parametrize(
        "cli_args, expected_code, expected_fragment",
        [
            ([], 1, "Подсказка: укажите выражение"),
            (["3 0 4 ~ 2 ~"], 0, "`3 0 4 ~ 2 ~ = 47`"),
            (["10", "5", "+"], 0, "`10 5 + = 15`"),
            (["20 0 /"], 1, "деление на ноль"),
            (["bad_input"], 1, "неизвестный символ"),
        ],
    )
    def test_cli_execution(self, cli_args, expected_code, expected_fragment, capsys):
        code = main(cli_args)
        assert code == expected_code
        output = capsys.readouterr().out
        assert expected_fragment in output

    def test_cli_reads_sys_argv(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["main.py", "4", "2", "/"])
        code = main()
        assert code == 0
        output = capsys.readouterr().out
        assert "`4 2 / = 2`" in output

    def test_direct_file_run(self, monkeypatch):
        import main as main_module
        file_path = str(Path(main_module.__file__).resolve())
        monkeypatch.setattr(sys, "argv", ["main.py", "6", "2", "*"])
        with pytest.raises(SystemExit) as exit_info:
            runpy.run_path(file_path, run_name="__main__")
        assert exit_info.value.code == 0