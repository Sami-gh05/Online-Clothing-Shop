from django import template

register = template.Library()

PERSIAN_TRANS = str.maketrans({
    "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
    "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
    ",": "٬",
})

@register.filter
def to_persian_digits(value):
    if value is None:
        return ""

    s = str(value).strip()
    if s == "":
        return ""

    # If separator already exists or output from other filters, just convert the digits
    if "," in s or "٬" in s:
        return s.translate(PERSIAN_TRANS)

    # Attempt to convert to number for thousand separator formatting
    try:
        # Also support "123.0" format (e.g., floatformat output)
        if "." in s:
            n = int(float(s))
        else:
            n = int(s)

        formatted = format(n, ",d")  # e.g., "1,234"
        return formatted.translate(PERSIAN_TRANS)

    except (ValueError, TypeError):
        # If not a number at all, at least convert the digits
        return s.translate(PERSIAN_TRANS)
