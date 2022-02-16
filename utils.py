D_EQUALITY_PRECISION = 1e-6


def curve_get_dy(payment_token_index, requested_token_index, payment_token_amount, token_amounts_before_payment,
                 amp, fee_percent):
    """
    calculate how much of a requested token to give to user for payment of a particular amount on another pool token.
    :param payment_token_index: the index of the token used as payment
    :param requested_token_index: the index of the token to be returned
    :param payment_token_amount: amount of payment token
    :param token_amounts_before_payment: array containing the amounts of tokens in the pool
    :param amp: The amplification factor
    :param fee_percent: Fee percent, e.g. 0.006
    :return: change (dy) in the amount of the requested token y in the pool
    """

    # changes in token amounts are c-units [?]
    y = curve_get_y(payment_token_index, requested_token_index,
                    token_amounts_before_payment[payment_token_index] + payment_token_amount,
                    token_amounts_before_payment, amp)

    dy = token_amounts_before_payment[requested_token_index] - y
    fee = dy * fee_percent
    dy = dy - fee
    return dy


def curve_get_y(payment_token_index, requested_token_index, token_amounts_after_payment,
                token_amounts_before_payment, amp) -> float:
    """
    calculates how much of the requested token should be in the pool after a payment which results in the total amount
    of the payment token to become x.
    :param payment_token_index: the index of the token used as payment
    :param requested_token_index: the index of the token to be returned
    :param token_amounts_after_payment: total amount of payment token in the pool after payment
    :param token_amounts_before_payment: amount of token in the pool before payment.
    :param amp: the amplification factor
    :return: total amount of the requested token in the pool after payment
    """
    # x in the input is converted to the same price/precision
    N_COINS = len(token_amounts_before_payment)
    assert payment_token_index != requested_token_index  # dev: same coin
    assert requested_token_index >= 0  # dev: j below zero
    assert requested_token_index < N_COINS  # dev: j above N_COINS
    # should be unreachable, but good for safety
    assert payment_token_index >= 0
    assert payment_token_index < N_COINS
    D = curve_get_D(token_amounts_before_payment, amp)
    c = D
    S_ = 0
    Ann = amp * N_COINS
    _x = 0
    _i = 0

    for _i in range(N_COINS) :
        if _i == payment_token_index:
            _x = token_amounts_after_payment
        elif _i != requested_token_index:
            _x = token_amounts_before_payment[_i]
        else:
            continue
        S_ += _x
        c = c * D / (_x * N_COINS)


    c = c * D / (Ann * N_COINS)
    b = S_ + D / Ann  # - D
    y_prev = 0
    y = D
    for _i in range(0, 254):
        y_prev = y
        y = (y * y + c) / (2 * y + b - D)
        # Equality with the precision of 1
        if y > y_prev:
            if y - y_prev <= 1:
                break
        else:
            if y_prev - y <= 1:
                break
    return y


def curve_get_D(x, A):
    """
    Calculate quantity D as noted in the StableSwap white paper.
    :param x: total amount of payment token in the pool
    :param A: amplification factor A as noted in the StableSwap white paper.
    :return: quantity D as noted in the StableSwap white paper
    """

    S = sum(x)

    D = S
    Ann = A * len(x)
    for c in range(0, 254):
        D_P = D

        for i in range(len(x)):
            D_P = D_P * D / (x[i] * len(x))

        Dprev = D
        D = (Ann * S + D_P * len(x)) * D / ((Ann - 1) * D + (len(x) + 1) * D_P)
        if D >= Dprev:
            if D - Dprev <= D_EQUALITY_PRECISION:
                break
            elif Dprev - D <= D_EQUALITY_PRECISION:
                break

    if abs(D - Dprev) > D_EQUALITY_PRECISION:
        print('Failed to find the right D for value', D)

    return D