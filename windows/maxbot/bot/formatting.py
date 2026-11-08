"""Преобразование школьных формул LaTeX в текст для MAX."""

from __future__ import annotations

import re


_TOKENS = re.compile(
    r"(?P<code>`{3}[\s\S]*?`{3}|`[^`\n]*`)"
    r"|(?P<block>(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$)"
    r"|(?P<bracket>\\\[[\s\S]*?\\\])"
    r"|(?P<paren>\\\([^\n]*?\\\))"
    r"|(?P<inline>(?<![\\$])\$(?!\$)[^$\n]+?(?<!\\)\$(?!\$))"
)
_COMMAND = re.compile(r"\\([a-zA-Z]+|[,;! ])")
_SYMBOLS = {
    "cdot": "·", "times": "×", "div": "÷", "pm": "±", "mp": "∓",
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠", "neq": "≠",
    "approx": "≈", "infty": "∞", "pi": "π", "alpha": "α", "beta": "β",
    "gamma": "γ", "delta": "δ", "Delta": "Δ", "theta": "θ", "lambda": "λ",
    "mu": "μ", "sigma": "σ", "omega": "ω", "sum": "∑", "int": "∫",
    "in": "∈", "notin": "∉", "to": "→", "rightarrow": "→",
    "Rightarrow": "⇒", "Leftrightarrow": "⇔", "ldots": "…", "dots": "…",
    "left": "", "right": "", "quad": " ", "qquad": " ",
    ",": " ", ";": " ", "!": "", " ": " ",
}
_SUPER = dict(zip("0123456789+-=()in", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁱⁿ"))
_SUB = dict(zip("0123456789+-=()aehijklmnoprstux", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤₓ"))


def _group(text: str, start: int) -> tuple[str, int] | None:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        return None
    depth = 1
    for end in range(start + 1, len(text)):
        if text[end] == "{":
            depth += 1
        elif text[end] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:end], end + 1
    return None


def _operand(text: str) -> str:
    return text if re.fullmatch(r"\w+", text) else f"({text})"


def _formula(text: str, depth: int = 0) -> str:
    # Ограничиваем вложенность формул из ответа модели.
    if depth >= 16:
        return text
    out: list[str] = []
    i = 0
    while i < len(text):
        command = _COMMAND.match(text, i)
        if command:
            name = command[1]
            first = _group(text, command.end())
            if name in {"frac", "dfrac", "tfrac"} and first:
                second = _group(text, first[1])
                if second:
                    numerator = _formula(first[0], depth + 1)
                    denominator = _formula(second[0], depth + 1)
                    out.append(f"{_operand(numerator)}/{_operand(denominator)}")
                    i = second[1]
                    continue
            if name in {"sqrt", "text", "mathrm", "mathbf", "operatorname"} and first:
                value = _formula(first[0], depth + 1)
                out.append("√" + _operand(value) if name == "sqrt" else value)
                i = first[1]
                continue
            out.append(_SYMBOLS.get(name, command[0]))
            i = command.end()
            continue
        if text[i] in {"^", "_"} and i + 1 < len(text):
            group = _group(text, i + 1)
            value, end = group if group else (text[i + 1], i + 2)
            value = _formula(value, depth + 1)
            alphabet = _SUPER if text[i] == "^" else _SUB
            if value and all(char in alphabet for char in value):
                out.append("".join(alphabet[char] for char in value))
            else:
                out.append(text[i] + f"({value})")
            i = end
            continue
        out.append(text[i])
        i += 1
    return "".join(out).strip()


def format_ai_text(text: str, *, markdown: bool = True) -> str:
    def replace(match: re.Match[str]) -> str:
        if match.lastgroup == "code":
            return match[0]
        width = 1 if match.lastgroup == "inline" else 2
        content = match[0][width:-width]
        # Цены вроде "$5 и $10" не считаем формулой.
        if match.lastgroup == "inline" and content != content.strip():
            return match[0]
        formula = _formula(content)
        if not formula:
            return match[0]
        if not markdown or "`" in formula:
            return formula
        # MAX сворачивает переносы внутри моноширинного фрагмента.
        return "\n".join(f"`{line}`" if line else "" for line in formula.splitlines())

    return _TOKENS.sub(replace, text)
