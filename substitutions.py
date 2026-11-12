"""Match ingredients against the substitutions stored in SQLite."""
import re


def suggest(ingredients, user, substitutions):
    result = []
    for line in ingredients.splitlines():
        changed = line
        # Leave ingredients already labelled as alternatives alone.
        if not re.search(r'plant|dairy.free|gluten.free|almond|soy milk|oat milk|coconut', line, re.I):
            for substitution in substitutions:
                if user[substitution['diet']]:
                    pattern = r'\b' + re.escape(substitution['ingredient']) + r'\b'
                    if re.search(pattern, line, re.I):
                        changed = re.sub(pattern, substitution['replacement'], line, flags=re.I)
                        break
        result.append((line, changed))
    return result
