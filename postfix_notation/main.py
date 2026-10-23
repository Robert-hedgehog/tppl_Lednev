import sys


def pf_add(a, b):
    return a + b


def pf_sub(a, b):
    return a - b


def pf_mul(a, b):
    return a * b


def pf_div(a, b):
    if b == 0:
        return None
    res = a / b
    return int(res) if res.is_integer() else res


def pf_tilde(a, b, stack):
    if a != 0 and b != 0:
        return abs(a - b)
    return (sum(stack) + a + b) ** 2

def pf_vosklzn(a, b):
    return a ** b


OPERATIONS = {
    "+": pf_add,
    "-": pf_sub,
    "*": pf_mul,
    "/": pf_div,
    "!": pf_vosklzn
}


def evaluate(expression: str):
    tokens = expression.split()
    if not tokens:
        print("Ошибка: строка пустая. Введите выражение через пробел.")
        return None

    stack = []
    print(f"\nВычисляем: `{expression}`")

    for step, token in enumerate(tokens, 1):
        if token in OPERATIONS or token == "~":
            if len(stack) < 2:
                print(f"Шаг {step}: для знака '{token}' не хватает чисел в стеке: {stack}")
                return None

            b = stack.pop()
            a = stack.pop()

            if token == "~":
                res = pf_tilde(a, b, stack)
                if a == 0 or b == 0:
                    stack.clear()
            else:
                res = OPERATIONS[token](a, b)
                if res is None:
                    print(f"Шаг {step}: ошибка — деление на ноль ({a} / 0).")
                    return None

            stack.append(res)
            print(f"Шаг {step}: '{token}' -> стек: {stack}")

        else:
            try:
                num = int(token)
            except ValueError:
                print(f"Шаг {step}: неизвестный символ '{token}'")
                return None

            stack.append(num)
            print(f"Шаг {step}: число {num} -> стек: {stack}")

    if len(stack) != 1:
        print(f"Ошибка: в стеке осталось {len(stack)} элементов: {stack}. Не хватает знаков операций.")
        return None

    return stack[0]


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if not args:
        print('Подсказка: укажите выражение. Пример: python main.py "3 0 4 ~ 2 ~"')
        return 1

    expr = " ".join(args)
    result = evaluate(expr)

    if result is not None:
        print(f"\n`{expr} = {result}`\n")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
