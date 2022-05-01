import copy
from utils.bucket_utils import create_buckets, print_buckets, print_list
from utils.datetime_utils import get_current_time, get_isoformat_date_str_from_datetime
from utils.trades.security_utils import print_openpos, security_symbol


## This is a function which assumes inventory transaction
def create_open_position_from_transaction(tx, selector_keys, transaction_split_keys):
    open_pos = {
        "quantity": tx['quantity'],
        "openTradeSplit": tx['tradeSplit'] if 'tradeSplit' in tx else False,
    }

    for key in selector_keys:
        open_pos[key] = tx[key]

    # This won't work for openpos fetched from db
    # for key in transaction_split_keys:
    #     open_pos[key] = tx[key]

    return open_pos


def split_transaction(transaction, quantity, split_keys):
    if quantity <= 0:
        raise RuntimeError("quantity {} cannot be less than or equal to 0".format(
            quantity
        ))

    if transaction['quantity'] <= quantity:
        raise RuntimeError("quantity {} cannot be greater than or equal to transaction['quantity'] {}".format(
            quantity, transaction['quantity']
        ))

    quantity_transaction = copy.deepcopy(transaction)
    quantity_transaction['quantity'] = quantity
    remaining_transaction = copy.deepcopy(transaction)
    remaining_transaction['quantity'] = transaction['quantity'] - quantity

    # The tradeSplit flag is used only to set the (open/close)TradeSplit flag in positions derived from trades
    quantity_transaction['tradeSplit'] = True
    remaining_transaction['tradeSplit'] = True

    split_ratio = quantity/transaction['quantity']

    for key in split_keys:
        if transaction[key]:
            quantity_transaction[key] = split_ratio * transaction[key]
            remaining_transaction[key] = transaction[key] - quantity_transaction[key]

    return quantity_transaction, remaining_transaction


def split_open_position(position, quantity, transaction_split_keys, openpos_split_keys):
    if quantity <= 0:
        raise RuntimeError("quantity {} cannot be less than or equal to 0".format(
            quantity
        ))

    if position['quantity'] <= quantity:
        raise RuntimeError("quantity {} cannot be greater than or equal to position['quantity'] {}".format(
            quantity, position['quantity']
        ))

    quantity_position = copy.deepcopy(position)
    quantity_position['quantity'] = quantity
    quantity_position['openTradeSplit'] = True
    remaining_position = copy.deepcopy(position)
    remaining_position['quantity'] = position['quantity'] - quantity
    remaining_position['openTradeSplit'] = True

    split_ratio = quantity/position['quantity']

    # This won't work for openpos fetched from db
    # for key in transaction_split_keys:
    #     if position[key]:
    #         quantity_position[key] = split_ratio * position[key]
    #         remaining_position[key] = position[key] - quantity_position[key]

    for key in openpos_split_keys:
        if position[key]:
            quantity_position[key] = split_ratio * position[key]
            remaining_position[key] = position[key] - quantity_position[key]

    return quantity_position, remaining_position


def create_closed_position(tx, open_pos, transaction_split_keys, openpos_split_keys, closed_pos_handler):
    rem_pos = None
    rem_tx = None

    if open_pos['quantity'] == tx['quantity']:
        quantity_pos = copy.deepcopy(open_pos)
        quantity_tx = copy.deepcopy(tx)
    elif open_pos['quantity'] > tx['quantity']:
        quantity_pos, rem_pos = split_open_position(open_pos, tx['quantity'], transaction_split_keys, openpos_split_keys)
        quantity_tx = copy.deepcopy(tx)
    else:
        quantity_pos = copy.deepcopy(open_pos)
        quantity_tx, rem_tx = split_transaction(tx, quantity_pos['quantity'], transaction_split_keys)

    closed_pos = copy.deepcopy(quantity_pos)
    closed_pos['closeTradeSplit'] = tx['tradeSplit'] if 'tradeSplit' in tx else False

    return closed_pos, rem_pos, rem_tx, quantity_tx


"""
    Description:
        The assumed keys in an object are:
            quanity - Quantity of item in Decimal
            match_info - tuple of (match_key in transaction,
                                   match_key in open position for opening trade type, 
                                   match_key in closed position for closing trade type, 
                                   [array of tuples. Each tuple represent trades of similar type.]
                                   ). 
            
            e.g.:tradeType - BUY/SELL
            match_info=('tradeType', 'openTradeType', 'closeTradeType', [('BUY',), ('SELL',)]),
            
            for transactionType - ('BUY', 'B', 'BUY TO OPEN') / ('SELL', 'S', 'SELL TO CLOSE')
            match_info=('transactionType', 'openTransactionType', 'closeTransactionType',
                            [('BUY', 'B', 'BUY TO OPEN'), ('SELL', 'S', 'SELL TO CLOSE')]),
            
            for entryType - DEBIT/CREDIT
            match_info=('type', 'openTradeType', 'closeTradeType', [('DEBIT',), ('CREDIT',)]),
            
    Parameters:
        transactions: sorted list of objects. An object is a python dictionary. Represents a trade.
        selector_keys: The keys in an object which are used to select item groups
                        For example: 
                        (stockItemName) in case of inventory
                        (securityName, securityType) in case of equity
                        (securityName, securityType, expirationDate) in case of futures
                        (securityName, securityType, expirationDate, optionType, strikePrice) in case of options
        open_positions: sorted list of objects. An object is a python dictionary. Represents an already open position.
        max_trades: It is a filter used for debugging.
        security_name: It is a filter used for debugging and creating report for a single equity.                      
"""


def compute_positions(transactions,
                      selector_keys,
                      transaction_split_keys,
                      open_positions,
                      openpos_split_keys,
                      match_info,
                      open_pos_handler=None,
                      closed_pos_handler=None,
                      max_trades=0,
                      security_name=None,
                      force_expire=False,
                      expiry_field='expiryDate',
                      processing_date=get_current_time(),
                      debug=False):
    # transactions is an array of unprocessed transactions
    # positions is an array of open positions before processing
    # At the end of this functions we will have closed positions and open_positions after processing

    tx_buckets = create_buckets(
        selector_keys,
        transactions
    )
    # print_buckets(tx_buckets, print_fn=print_transaction, title="Transactions buckets:")

    positions_buckets = create_buckets(
        selector_keys,
        open_positions
    )
    # print_buckets(positions_buckets, print_fn=print_openpos, title="Positions buckets:")

    tx_match_key = match_info[0]
    openpos_match_key = match_info[1]
    closepos_match_key = match_info[2]
    match_groups = match_info[3]

    ## NG: Temp Change
    security_name_filer = None
    if security_name:
        security_name_filer = [(security_name, 'EQ')]

    closed_positions = []
    created_updated_open_positions = []
    consumed_open_positions = []


    for selector, sec_tx_bucket in tx_buckets.items():
        if security_name_filer and selector not in security_name_filer:
            continue

        sec_closed_positions = []
        sec_consumed_open_positions = []
        if not selector in positions_buckets:
            positions_buckets[selector] = []
        sec_open_positions = positions_buckets[selector]

        for pos in sec_open_positions:
            pos['created'] = False
            pos['modified'] = False

        trade_count = 0
        for tx in sec_tx_bucket:
            tx['quantity'] = abs(tx['quantity'])

            for key in transaction_split_keys:
                tx[key] = abs(tx[key])

            if debug:
                print_transaction(tx, title="compute_positions: tx[{}]".format(trade_count))

            rem_tx = tx

            while rem_tx:
                if len(sec_open_positions) == 0 or \
                        is_same_group(tx, sec_open_positions[0], tx_match_key, openpos_match_key, match_groups
                                      ):
                    open_pos = create_open_position_from_transaction(rem_tx, selector_keys, transaction_split_keys)
                    open_pos[openpos_match_key] = rem_tx[tx_match_key]
                    # open_pos = copy.deepcopy(rem_tx)

                    if open_pos_handler:
                        open_pos_handler('created', open_pos, transaction=rem_tx)

                    open_pos['created'] = True
                    open_pos['modified'] = False
                    sec_open_positions.append(open_pos)
                    rem_tx = None
                else:
                    # print("We need to create a closed position")
                    open_pos = sec_open_positions.pop(0)
                    open_pos['modified'] = True
                    if debug:
                        print_openpos(open_pos, title="Popped Open Position")

                    closed_pos, rem_pos, new_rem_tx, quantity_tx = create_closed_position(rem_tx,
                                                                         open_pos,
                                                                         transaction_split_keys,
                                                                         openpos_split_keys,
                                                                         closed_pos_handler)
                    closed_pos[closepos_match_key] = rem_tx[tx_match_key]

                    if closed_pos_handler:
                        closed_pos_handler(closed_pos, quantity_tx)

                    if debug:
                        if new_rem_tx:
                            print_transaction(new_rem_tx, title="Remaining Tx:")

                    sec_closed_positions.append(closed_pos)
                    if rem_pos:
                        sec_open_positions.insert(0, rem_pos)
                        open_pos_handler('modified', rem_pos, transaction=rem_tx, closed_pos=closed_pos)
                    else:
                        open_pos_handler('deleted', open_pos, transaction=rem_tx, closed_pos=closed_pos)
                        if not open_pos['created']:
                            sec_consumed_open_positions.append(open_pos)


                    rem_tx = new_rem_tx

            trade_count += 1
            if max_trades > 0:
                if trade_count >= max_trades:
                    break

        # Check for open trades which are expired
        remaining_open_positions = list(filter(lambda pos: pos['created'] or pos['modified'], sec_open_positions))

        if len(remaining_open_positions) > 0:
            if force_expire:
                expiry_date = selector[selector_keys.index(expiry_field)]
                if expiry_date is not None:
                    if expiry_date < processing_date:
                        if debug or True:
                            print("Position {} expired expiry_date={}".format(
                                security_symbol(remaining_open_positions[0]),
                                get_isoformat_date_str_from_datetime(expiry_date)
                            ))
                            # print_list(remaining_open_positions, print_openpos, 'Remaining Open Positions: {}'.format(selector))
                        # We need to create a trade for the expired position
        else:
            if debug:
                print("No Remaining Positions: {}".format(selector))

        # Append the closed and open positions to the common array
        closed_positions.extend(sec_closed_positions)
        created_updated_open_positions.extend(remaining_open_positions)
        consumed_open_positions.extend(sec_consumed_open_positions)


    for pos in created_updated_open_positions:
        del pos['created']
        del pos['modified']

    for pos in consumed_open_positions:
        del pos['created']
        del pos['modified']

    for pos in closed_positions:
        del pos['created']
        del pos['modified']

    return closed_positions, created_updated_open_positions, consumed_open_positions


def get_match_group(match_value, match_groups):
    result = None
    for group in match_groups:
        if match_value in group:
            result = group
            break
    return result


def is_same_group(transaction, open_pos, tx_match_key, openpos_match_key, match_groups):
    # print("Returning match using match_info: ")
    openpos_group =  get_match_group(open_pos[openpos_match_key].upper(), match_groups)
    if openpos_group is None:
        raise RuntimeError("{} '{}' does not belong to any match groups".format(
            openpos_match_key, open_pos[openpos_match_key])
        )

    transaction_group =  get_match_group(transaction[tx_match_key].upper(), match_groups)
    if transaction_group is None:
        raise RuntimeError("{} '{}' does not belong to any match groups".format(
            tx_match_key, transaction[tx_match_key])
        )

    return openpos_group == transaction_group
