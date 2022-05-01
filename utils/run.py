# For exec
run_code_result = -1


def run_code(type, code, input, debug=False):
    if debug:
        print("run_code(): type(input)={} input={} ".format(input.__class__, input))

    if type == 'exec':
        execCode = compile(code, 'mutlistring', type)
        exec(execCode)
        if debug:
            print("run_code: run_code_result = {}".format(run_code_result))
        result = run_code_result

    elif type == 'eval':
        # Need to understand more about this and how this is to be used
        evalCode = compile(code, 'mutlistring', type)
        result = eval(evalCode)
        if debug:
            print('run_code:eval result={}'.format(result))

    else:
        raise RuntimeException('Type {} for code not supported yet'.format(type))

    if debug:
        print("run_code:result = {}".format(result))

    return result