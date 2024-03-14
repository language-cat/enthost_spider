def maketrans(from_text, to_text):
    return dict((ord(i), n) for i, n in zip(from_text, to_text))


def formula_trans(mf):
    if not isinstance(mf, str):
        return None
    from_t = u"₀₁₂₃₄₅₆₇₈₉"
    to_t = u'0123456789'
    return mf.translate(maketrans(from_t, to_t))
