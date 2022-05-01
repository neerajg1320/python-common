import copy


def print_list(rList, print_fn=None, title=None):
    if title:
        print(title, ": Empty()" if len(rList) == 0 else "")
    for elm in rList:
        if print_fn:
            print_fn(elm)
        else:
            print(elm)


def create_buckets(selector_keys, rlist):
    buckets = {}
    for elm in rlist:
        selector_list = []
        for key in selector_keys:
            selector_list.append(elm[key])
        selector = tuple(selector_list)
        # print(selector)

        if not selector in buckets:
            buckets[selector] = []
        buckets[selector].append(elm)

    return buckets


def print_buckets(buckets, print_fn=None, title=None, summary_fn=None):
    if title:
        print(title, ": Empty()" if len(buckets) == 0 else "")

    summary_total = None
    for k, v in buckets.items():
        print('key:', k)
        for elm in v:
            if print_fn:
                print_fn(elm)
            else:
                print(elm)

            if summary_fn:
                summary_vars = summary_fn(elm)
                if not summary_total:
                    summary_total = copy.deepcopy(summary_vars)
                else:
                    for i in range(len(summary_total)):
                        summary_total[i] += summary_vars[i]

    if summary_total:
        print('Total:  ', end="")
        [print("{:16.2f}".format(var), end="") for var in summary_total]
        print()
