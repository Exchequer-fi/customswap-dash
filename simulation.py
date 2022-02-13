from src.liquidity_pool import LiquidityPool
from copy import deepcopy
import numpy as np


def perform_simulation(a1=85, a2=0.0001):

    def compute_prices(lps, payment_token_label, requested_token_label, reverse_slippage=False):

        # copy to prevent side-effects outside the function
        lps = [deepcopy(lp) for lp in lps]

        n_pricing_methods = len(lps)
        num_tokens = len(token_labels)
        totals = np.zeros((n_pricing_methods, n_purchases))
        received_amounts = np.zeros((n_pricing_methods, n_purchases))
        prices = np.zeros((n_pricing_methods, n_purchases))
        Ds = np.zeros((n_pricing_methods, n_purchases))
        token_amounts = np.zeros((n_pricing_methods, n_purchases, num_tokens))
        amplifications = np.zeros((n_pricing_methods, n_purchases))
        price_slippages = np.zeros((n_pricing_methods, n_purchases))

        total = 0
        for i in range(n_purchases):
            total += purchase_each_time
            for p in range(n_pricing_methods):
                totals[p, i] = total
                price_slippages[p, i] = lps[p].get_price_slippage(payment_token_label=payment_token_label,
                                                                  requested_token_label=requested_token_label,
                                                                  payment_token_amount=purchase_each_time,
                                                                  reverse_slippage=reverse_slippage)
                received_amounts[p, i] = lps[p].exchange(payment_token_label=payment_token_label,
                                                         requested_token_label=requested_token_label,
                                                         payment_token_amount=purchase_each_time)
                prices[p, i] = lps[p].get_price(payment_token_label=payment_token_label,
                                                requested_token_label=requested_token_label)
                Ds[p, i] = lps[p].get_D()
                amplifications[p, i] = lps[p].get_last_amplification()
                token_amounts[p, i] = lps[p]._token_amounts

        return totals, prices, received_amounts, Ds, amplifications, token_amounts, price_slippages

    token_labels = ['Boot', 'USDC']

    initial_token_amounts = [50000, 50000]

    lp_customswap1 = LiquidityPool(token_labels, initial_token_amounts, fee_ratio=0,
                                   pricing_method='customswap', amplification=[a1, a2], promoted_token_label='Boot')

    lp_uniswap = LiquidityPool(token_labels, initial_token_amounts, fee_ratio=0,
                               pricing_method='uniswap')

    lp_stableswap = LiquidityPool(token_labels, [50000, 50000], fee_ratio=0,
                                  pricing_method='stableswap', amplification=a1)

    lps = [lp_uniswap, lp_stableswap, lp_customswap1]

    n_purchases = 10
    purchase_each_time = 5000

    totals1, prices1, received_amounts1, Ds1, amplifications1, token_amounts1, price_slippages1 = \
        compute_prices(lps, payment_token_label='Boot', requested_token_label='USDC')

    totals2, prices2, received_amounts2, Ds2, amplifications2, token_amounts2, price_slippages2 = \
        compute_prices(lps, payment_token_label='USDC', requested_token_label='Boot')

    prices1 = 1 / np.flip(prices1, axis=-1)
    price_slippages1 = np.flip(price_slippages1, axis=-1)

    token_ratio1 = token_amounts1[:, :, 1] / token_amounts1[:, :, 0]
    token_ratio2 = token_amounts2[:, :, 1] / token_amounts2[:, :, 0]

    token_ratio1 = np.flip(token_ratio1, axis=1)

    amplifications1 = np.flip(amplifications1, axis=-1)

    return prices1, prices2, price_slippages1, price_slippages2, token_ratio1, token_ratio2, \
           amplifications1, amplifications2
