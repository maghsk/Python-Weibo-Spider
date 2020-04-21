import numpy as np

def dis(a, b, verbose=False):
    '''
    :param a: 字符串 a
    :param b: 字符串 b
    :param verbose: 是否开启啰嗦模式
    :return: a 与 b 的最小编辑距离
    '''
    a = a + '，'
    b = b + '。'
    dp = np.ones(shape=(len(a) + 1, len(b) + 1), dtype=np.int) * (len(a) + len(b)) * 2
    dp[0][0] = 0
    for i in range(len(a)):
        for j in range(len(b)):
            dp[i + 1][j] = min(dp[i + 1][j], dp[i][j] + 1)
            dp[i][j + 1] = min(dp[i][j + 1], dp[i][j] + 1)
            dp[i + 1][j + 1] = min(dp[i + 1][j + 1], dp[i][j] + (2 if a[i] != b[j] else 0))
    if verbose:
        print(dp)
    return dp[len(a)-1][len(b)-1]

if __name__ == '__main__':
    print(dis('蛋白酶', '化酶', verbose=True))
