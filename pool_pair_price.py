import numpy as np
from liquidity_pool import LiquidityPool


def final_price_for_liquidity_ratio(uniswap_liquity_ratio, arb_trade_boot_num=100,
                                    large_sell_ratio=0.1, boot_token_num=50000, amplification=None,
                                    arb_price_tolerance=0.03, large_uniswap_trade=True):

    # computes final price, after arbs, when a large sell trade happens in (Customswap, Uniswap) liquidity pool pair.

    token_labels = ['Boot', 'USDC']

    if amplification is None:
        amplification = [85, 0.0001]

    # equal amount Boot and USDC, price = $1 per Boot
    initial_token_amounts = np.array([boot_token_num, boot_token_num])

    uniswap_token_amounts = np.round(uniswap_liquity_ratio * initial_token_amounts)
    customswap_token_amounts = initial_token_amounts - uniswap_token_amounts

    lp_uniswap = LiquidityPool(token_labels, uniswap_token_amounts, fee_ratio=0, pricing_method='uniswap')
    lp_customswap = LiquidityPool(token_labels, customswap_token_amounts, fee_ratio=0,
                                  pricing_method='customswap', amplification=amplification,
                                  promoted_token_label='Boot')

    # Perform one large sell trade of Boot token in Uniswap or Customswap pool
    large_sell_num_tokens = initial_token_amounts[0] * large_sell_ratio

    if large_uniswap_trade:
        # large sale trade in Uniswap
        lp_uniswap.get_price(payment_token_label='USDC',
                             requested_token_label='Boot')

        returned_token_amount = lp_uniswap.exchange(payment_token_label='Boot',
                            requested_token_label='USDC',
                            payment_token_amount=large_sell_num_tokens)

        lp_uniswap.get_price(payment_token_label='USDC',
                             requested_token_label='Boot')
    else:  # large sale trade in Customswap
        lp_customswap.get_price(payment_token_label='USDC',
                                requested_token_label='Boot')

        returned_token_amount = lp_customswap.exchange(payment_token_label='Boot',
                               requested_token_label='USDC',
                               payment_token_amount=large_sell_num_tokens)

        lp_customswap.get_price(payment_token_label='USDC',
                                requested_token_label='Boot')

    effective_large_sell_price = returned_token_amount / large_sell_num_tokens

    # arbitrage simulation between the two pools until the price become very similar (to ~3% of each other)

    uniswap_prices_before_arb = []
    customswap_prices_before_arb = []
    received_boot_amounts = []
    received_usdc_amounts = []
    uniswap_prices_after_arb = []
    customswap_prices_after_arb = []
    arbBootGains = []

    while len(uniswap_prices_after_arb) == 0 or len(customswap_prices_after_arb) == 0 or \
            abs(customswap_prices_before_arb[-1] - uniswap_prices_before_arb[-1]) / \
            ((customswap_prices_before_arb[-1] + uniswap_prices_before_arb[-1]) / 2) > arb_price_tolerance:

        uniswap_prices_before_arb.append(lp_uniswap.get_price(payment_token_label='USDC',
                                                              requested_token_label='Boot'))

        customswap_prices_before_arb.append(lp_customswap.get_price(payment_token_label='USDC',
                                                                    requested_token_label='Boot'))

        # if price of Boot token in Customswap is higher, then sell some Boot there, then use the USDC money to
        # buy token on Uniswap (increasing price)
        if customswap_prices_before_arb[-1] > uniswap_prices_before_arb[-1]:

            received_usdc_amount = lp_customswap.exchange(payment_token_label='Boot',
                                                          requested_token_label='USDC',
                                                          payment_token_amount=arb_trade_boot_num)

            received_boot_amount = lp_uniswap.exchange(payment_token_label='USDC',
                                                       requested_token_label='Boot',
                                                       payment_token_amount=received_usdc_amount)

            arbBootGains.append(received_boot_amount - arb_trade_boot_num)

        # if price of Boot token in Uniswap is higher, then sell some Boot there, then use the USDC money to
        # buy token on Customswap (increasing price)
        elif customswap_prices_before_arb[-1] < uniswap_prices_before_arb[-1]:
            received_usdc_amount = lp_uniswap.exchange(payment_token_label='Boot',
                                                       requested_token_label='USDC',
                                                       payment_token_amount=arb_trade_boot_num)

            received_boot_amount = lp_customswap.exchange(payment_token_label='USDC',
                                                          requested_token_label='Boot',
                                                          payment_token_amount=received_usdc_amount)

            arbBootGains.append(received_boot_amount - arb_trade_boot_num)

        received_boot_amounts.append(received_boot_amount)
        received_usdc_amounts.append(received_usdc_amount)

        uniswap_prices_after_arb.append(lp_uniswap.get_price(payment_token_label='USDC',
                                                             requested_token_label='Boot'))

        customswap_prices_after_arb.append(lp_customswap.get_price(payment_token_label='USDC',
                                                                   requested_token_label='Boot'))

    if large_uniswap_trade:
        return uniswap_prices_after_arb[-1], np.sum(arbBootGains), effective_large_sell_price
    else:
        return customswap_prices_after_arb[-1], np.sum(arbBootGains), effective_large_sell_price


def compute_market_cap_saved(boot_total_token_num, large_sell_ratio=0.1, boot_pool_token_num=1000000,
                             large_uniswap_trade=True,
                             arb_trade_boot_num=50, arb_price_tolerance=0.03, amplification=None):

    # compute market cap saved by adding Customswap compared to if all the liquidity was in a Uniswap pool.

    uniswap_liquity_ratios = np.arange(0.05, 0.99, 1 / 30)

    final_prices_for_liquidity_ratio = []
    arb_drains = []
    effective_large_sell_prices = []
    for uniswap_liquity_ratio in uniswap_liquity_ratios:
        final_price, arb_drain, effective_large_sell_price = final_price_for_liquidity_ratio(uniswap_liquity_ratio,
                                                                 large_sell_ratio=large_sell_ratio,
                                                                 arb_trade_boot_num=arb_trade_boot_num,
                                                                 boot_token_num=boot_pool_token_num,
                                                                 arb_price_tolerance=arb_price_tolerance,
                                                                 large_uniswap_trade=large_uniswap_trade,
                                                                 amplification=amplification)
        final_prices_for_liquidity_ratio.append(final_price)
        arb_drains.append(arb_drain)
        effective_large_sell_prices.append(effective_large_sell_price)

    price_if_all_uniswap, _, _ = final_price_for_liquidity_ratio(0.999,
                                                           large_sell_ratio=large_sell_ratio,
                                                           arb_trade_boot_num=1)

    final_prices_for_liquidity_ratio = np.array(final_prices_for_liquidity_ratio)
    market_cap_saved = (final_prices_for_liquidity_ratio - price_if_all_uniswap) * boot_total_token_num


    return market_cap_saved, final_prices_for_liquidity_ratio, uniswap_liquity_ratios, price_if_all_uniswap, \
           arb_drains, effective_large_sell_prices


def plot_saved_market_cap():
    # create final price and market cap saved plots.
    import matplotlib.pyplot as plt
    import matplotlib

    for large_uniswap_trade in [True, False]:

        market_cap_saved_uni, final_prices_for_liquidity_ratio_uni, uniswap_liquity_ratios_uni, price_if_all_uniswap_uni = \
            compute_market_cap_saved(large_uniswap_trade=large_uniswap_trade, arb_trade_boot_num=50,
                                         arb_price_tolerance=0.03)


        large_sell_ratio = 0.1
        plt.figure(figsize=(20, 10))
        plt.rcParams.update({'font.size': 22})

        plt.plot(uniswap_liquity_ratios_uni, final_prices_for_liquidity_ratio_uni, 'o-')
        plt.xlabel('Pool ratio in Uniswap')

        plt.ylabel('Price after %d percent sale of Boot' % round(100 * large_sell_ratio))

        if large_uniswap_trade:
            plt.title('Boot sale in Uniswap')
        else:
            plt.title('Boot sale in Customswap')

        plt.show()

        plt.figure(figsize=(20, 10))
        plt.plot(uniswap_liquity_ratios_uni, market_cap_saved_uni, 'o-', color='k')
        plt.xlabel('Pool ratio in Customswap')
        plt.ylabel('Markep cap saved ($)')
        plt.gca().get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda x, p: format(int(x), ',')))
        plt.show()