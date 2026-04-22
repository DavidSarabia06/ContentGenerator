def print_boxed_message(
    message: str,
    border_symbol: str = "#",
    color: str = "default",
    bold: bool = False
):
    colors = {
        "default": "\033[0m",
        "red":     "\033[91m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "blue":    "\033[94m",
        "magenta": "\033[95m",
        "cyan":    "\033[96m",
        "white":   "\033[97m",
    }

    color_code = colors.get(color.lower(), colors["default"])
    bold_code = "\033[1m" if bold else ""
    reset_code = "\033[0m"

    padding = 2
    line_length = len(message) + padding * 2 + 4
    border_line = border_symbol * line_length
    middle_line = f"{border_symbol}{border_symbol}{' ' * padding}{message}{' ' * padding}{border_symbol}{border_symbol}"

    print(color_code + bold_code + border_line)
    print(middle_line)
    print(border_line + reset_code)
    print()

def print_subline_message(
    message: str,
    border_symbol: str = "#",
    color: str = "default",
    bold: bool = False
):
    colors = {
        "default": "\033[0m",
        "red":     "\033[91m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "blue":    "\033[94m",
        "magenta": "\033[95m",
        "cyan":    "\033[96m",
        "white":   "\033[97m",
    }

    color_code = colors.get(color.lower(), colors["default"])
    bold_code = "\033[1m" if bold else ""
    reset_code = "\033[0m"

    padding = 2
    line_length = len(message) + padding * 2 + 3
    border_line = border_symbol * line_length
    middle_line = f"{border_symbol}{' ' * padding}{message}{' ' * padding}{border_symbol}"

    print(color_code + bold_code + border_line)
    print(middle_line)
    print(border_line + reset_code)
    print()

def print_color_message(
    message: str,
    color: str = "default",
):
    colors = {
        "default": "\033[0m",
        "red":     "\033[91m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "blue":    "\033[94m",
        "magenta": "\033[95m",
        "cyan":    "\033[96m",
        "white":   "\033[97m",
    }

    color_code = colors.get(color.lower(), colors["default"])

    print(color_code + message)
    print()
