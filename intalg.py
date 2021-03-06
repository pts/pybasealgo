#! /usr/bin/python2.6

"""Number theory and other integer algorithms in pure Python 2.x.

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

Works with Python 2.4, 2.5, 2.6 and 2.7. Developed using Python 2.6. Doesn't
work with Python 3.x.

Functions in this module don't use floating point calculations unless the
docstring of the function mentions float.

This module assumes that `/' on integers rounds down. (Not true in Python
3.x.)

Python has arbitrary precision integers built-in: the long type.

Python has arbitrary precision rationals: fractions.Fraction.

Python has arbitrary precision decimal floating point numbers:
decimal.Decimal. The target precision has to be set before the operations,
the default is 28 digits after the dot.

Python has modular exponentiation built-in: pow(a, b, c).
"""

# TODO(pts): Add more unit tests.
# TODO(pts): Try http://pypi.python.org/pypi/NZMATH/1.1.0
# TODO(pts): Document https://github.com/epw/pyfactor/blob/master/factor.c
# TODO(pts): Pollard Rho and Pollard p-1 in sympy (sympy/ntheory/factor_.py)
# TODO(pts): Use C extensions (or sympy etc.), if available, for faster operation (especially prime factorization and prime tests).
# TODO(pts): perfect_power etc. in sympy/ntheory/factor_.py
# TODO(pts): Copy fast gcd from pyecm.py. Is it that fast?
#   Maybe faster in C, but not in Python.
#   http://en.wikipedia.org/wiki/Binary_GCD_algorithm
# TODO(pts): Use faster C modules for all algorithms, e.g.
#   C code for prime factorization etc. Use gmpy (has gmpy.is_prime for primt
#   detection and gmpy.mpq to replace fractions.Fraction), python-gmp,
#   numpy, sympy, sage (?), scipy. Example:
#   from gmpy import gcd, invert, mpz, next_prime, sqrt, root.
# TODO(pts): Add invert (modular inverse) from pyecm. Isn't that too long?
# TODO(pts): pyecm.py has a strange next_prime implementation. Is it faster?
#   How does it work? Copy it. Does it contain an inlined Rabin-Miller test?

__author__ = 'pts@fazekas.hu (Peter Szabo)'

import array
import bisect
import _random
import struct


_HEX_BIT_COUNT_MAP = {
    '0': 0, '1': 1, '2': 2, '3': 2, '4': 3, '5': 3, '6': 3, '7': 3}


def bit_count(a):
  """Returns the number of bits needed to represent abs(a). Returns 1 for 0."""
  if not isinstance(a, (int, long)):
    raise TypeError
  if not a:
    return 1
  # Example: hex(-0xabc) == '-0xabc'. 'L' is appended for longs.
  # TODO(pts): Would s = bin(a) be faster?
  # See also
  # http://stackoverflow.com/questions/2654149/count-bits-of-a-integer-in-python/13663234
  s = hex(a)
  d = len(s)
  if s[-1] == 'L':
    d -= 1
  if s[0] == '-':
    d -= 4
    c = s[3]
  else:
    d -= 3
    c = s[2]
  return _HEX_BIT_COUNT_MAP.get(c, 4) + (d << 2)


# Use int.bit_length and long.bit_length introduced in Python 2.7 and 3.x.
if getattr(0, 'bit_length', None):
  __doc = bit_count.__doc__
  def bit_count(a):
    return a.bit_length() or 1
  bit_count.__doc__ = __doc


def sqrt_floor(n):
  """Returns like int(math.sqrt(n)), but correct for very large n.

  Uses Newton-iteration.
  """
  # This is like Newton-iteration, but all divisions are rounding down to
  # the nearest integer, so it handles +-1 fluctuations caused by the
  # rounding errors.
  if n < 4:
    if n < 0:
      raise ValueError('Negative input for square root.')
    if n:
      return 1
    else:
      return 0
  #if n < (1 << 328):
  #  # This is a bit faster than computing bit_count(n), but checking the
  #  # condition is slow.
  #  low = 2
  #  high = n >> 1
  b = a = 1 << ((bit_count(n) - 1) >> 1)  # First approximation.
  a = (a + n / a) >> 1; c = a; a = (a + n / a) >> 1
  while a != b:
    b = a; a = (a + n / a) >> 1; c = a; a = (a + n / a) >> 1
  if a < c:
    return int(a)
  else:
    return int(c)


def root_floor(n, k):
  """Finds the floor of the kth root of n.

  Based on the root(...) function in pyecm.py, which is based on gmpy's root(...)
  function.

  Uses Newton-iteration.

  For k == 2, uses exactly the same algorithm as sqrt_floor, and it's only a
  tiny bit slower.

  Returns:
    A tuple (r, is_exact), where r is the floor of the kth root of n, and
    is_exact is a bool indicating whether the root is exact, i.e. r ** k == n.
  """
  if k <= 0 or n < 0:
    raise ValueError
  if k == 1 or n <= 1:
    return int(n), True
  if k == 2:  # Fast Newton-iteration to compute the square root.
    #if n < (1 << 328):
    #  # This is a bit faster than computing bit_count(n), but checking the
    #  # condition is slow.
    #  low = 2
    #  high = n >> 1
    b = a = 1 << ((bit_count(n) - 1) >> 1)  # First approximation.
    a = (a + n / a) >> 1; c = a; a = (a + n / a) >> 1
    while a != b:
      b = a; a = (a + n / a) >> 1; c = a; a = (a + n / a) >> 1
    if a < c:
      return int(a), a * a == n
    else:
      return int(c), c * c == n
  if not (n >> k):  # 2 <= n < 2 ** k
    return 1, False
  # Now: n >= 2, k >= 3, n >= 2 ** k >= 8.

  # Use the base-2 length of n to narrow the [low, high) interval:
  # the return value will have about bit_count(n) / k bits.
  c = bit_count(n)
  b = (c - 1) / k
  if b > 1:
    # True: assert 2 <= 1 << b < 2 << b <= (n >> 2) + 1
    low = 1 << b
    high = 2 << b
  else:
    low = 2
    high = 4 - (c <= 4)  # c == 4 iff 8 <= n <= 15.

  # Use Newton-iteration to quickly narrow the [low, high) interval.

  x = low
  k1 = k - 1
  # Newton-iteration for f(x)  = x ** k - n:
  # y = x - f(x) / f'(x) = x - (x ** k - n) / (k * x ** (k - 1)) =
  #   = x - x / k + n / x ** (k - 1) / k ==
  #   = (x * (k - 1) + n / x ** (k - 1)) / k
  # Our y is less accurate, because the division truncates.
  # TODO(pts): Try rounding up -- or proper rounding. Does it speed it up?
  y = (k1 * x + n / x ** k1) / k
  # For example: with root_floor(3 ** 1000, 1000), y is insanely large, but
  # high is just 4, so fit y.
  if y < low or y >= high:
    y = (low + high) >> 1
  while True:
    z = (k1 * y + n / y ** k1) / k
    mr = cmp(z ** k, n)
    if mr < 0:
      if low < z:  # It seems to be always `low <= z', but we can't prove it.
        low = z
    elif mr:
      if high > z:  # z <= high is not always true.
        high = z
    else:
      return int(z), True
    if abs(z - y) >= abs(x - y):  # We can't make any more improvements.
      # Maybe z is the correct return. Adjust `high', because we couldn't do
      # that because of the roundings.
      if y == z and high > z + 1 and (z + 1) ** k > n:
        high = z + 1
      break
    x, y = y, z

  # Do a binary search as fallback if Newton-iteration wasn't accurate enough.
  # Usually low and high are very close to each other by now, and we have to
  # do only a few steps.

  # Now (and after each iteration) `low <= root(n, k) < high', which is
  # equivalent to `low <= floor(root(n, k)) < high', which is equivalent to
  # `low <= retval < high'. So we can stop the loop iff high == low + 1.
  while high > low + 1:
    # True: assert low ** k <= n < high ** k
    mid = (low + high) >> 1
    # True: assert low < mid < high
    mr = cmp(mid ** k, n)
    if mr < 0:
      low = mid
    elif mr:
      high = mid
    else:
      return int(mid), True
  return int(low), False


A0 = array.array('b', (0,))
"""Helper for primes_upto."""

A1 = array.array('b', (1,))
"""Helper for primes_upto."""


_prime_cache = []
_prime_cache_limit_ary = [1]


def clear_prime_cache():
  _prime_cache_limit_ary[:] = [1]  # For thread safety.
  del _prime_cache[:]


def ensure_prime_cache_upto(limit):
  """Ensures that all primes p for which 2 <= p <= limit are in the prime cache.

  Please note that it's expensive to increase the prime cache size, because
  for that _prime_cache has to recomputed for scratch, so if you increase by
  small amounts many times, then please round up to the next power of 2 etc.

  After this function returns, this will be true:

    assert _prime_cache_limit_ary[0] >= limit
  """
  if _prime_cache_limit_ary[0] < limit:
    _prime_cache[:] = primes_upto(limit)
    # For thread safety and for good _prime_cache interaction between
    # primes_upto and prime_index, set this after updating _prime_cache.
    _prime_cache_limit_ary[0] = limit


def ensure_prime_cache_size(n):
  """Ensures that there are at least n primes in the prime cache.

  Please note that it's expensive to increase the prime cache size, because
  for that _prime_cache has to recomputed for scratch, so if you increase by
  small amounts many times, then please round up to the next power of 2 etc.

  After this function returns, this will be true:

    assert len(_prime_cache) >= n
  """
  if len(_prime_cache) < n:
    ensure_prime_cache_upto(prime_idx_more(n))
    assert len(_prime_cache) >= n


def primes_upto(n):
  """Returns a list of prime numbers <= n using the sieve algorithm.

  Please note that it uses O(n) memory for the returned list, and O(n) (a
  list of at most n / 2 items) for a temporary bool array.
  """
  if n <= 1:
    return []
  if n <= _prime_cache_limit_ary[0]:
    cache = _prime_cache
    return cache[:bisect.bisect_right(cache, n)]
  # Based on http://stackoverflow.com/a/3035188/97248
  # Made it 7.04% faster and use much less memory by using array('b', ...)
  # instead of lists.
  #
  # TODO(pts): Use numpy if available (see the solution there).
  n += 1
  s = A1 * (n >> 1)
  a0 = A0
  for i in xrange(3, sqrt_floor(n) + 1, 2):
    if s[i >> 1]:
      ii = i * i
      # itertools.repeat makes it slower by about 12%.
      s[ii >> 1 : : i] = a0 * ((((n - ii - 1) / i) >> 1) + 1)
  s = [(i << 1) | 1 for i in xrange(n >> 1) if s[i]]
  s[0] = 2  # Change from 1.
  return s


def yield_primes():
  """Yields all primes (indefinitely).

  Uses O(sqrt(n)) memory to yield the first n primes.
  """
  # Based on the postponed sieve implementation by Will Ness on
  # http://stackoverflow.com/a/10733621/97248 .
  yield 2; yield 3; yield 5; yield 7
  d = {}
  c = 9
  ps = yield_primes()
  p = ps.next() and ps.next()  # 3.
  q = p * p                    # 9.
  while 1:
    if c not in d:
      if c < q:
        yield c
      else:
        s = 2 * p
        x = c + s
        while x in d:
          x += s
        d[x] = s
        p = ps.next()
        q = p * p
    else:
      s = d.pop(c)
      x = c + s
      while x in d:
        x += s
      d[x] = s
    c += 2


def yield_primes_upto(n):
  """Yields primes <= n.

  Slower (by a factor of about 5.399) than primes_upto(...), but uses only
  O(sqrt(prime_count(n))) memory (instead of O(n)), where pi(n) is the
  number of primes <= n.
  """
  # TODO(pts): Add some kind of caching variant.
  #
  # itertools.takewhile(lambda x: x < n, yield_primes()) was tried, but it
  # 1.419% (slightly) faster.
  for p in yield_primes():
    if p > n:
      break
    yield p


def yield_first_primes(i):
  """Yields the first i primes.

  Uses O(sqrt(i)) temporary memory, because it uses yield_primes().
  """
  # TODO(pts): Add a variant based on primes_upto, possibly
  # doing a bit more than sqrt(i) sieve steps.
  y = yield_primes()
  for i in xrange(0, i):
    yield y.next()


def yield_composites():
  """Yields composite numbers in increasing order from 4."""
  n = 4
  for p in yield_primes():
    while n < p:
      yield n
      n += 1
    n = p + 1


# struct.pack('>257H', *([0] + [int(math.ceil(math.log(i)/math.log(2)*256)) for i in xrange(1, 257)]))
LOG2_256_MORE_TABLE = struct.unpack('>257H',
    '\x00\x00\x00\x00\x01\x00\x01\x96\x02\x00\x02S\x02\x96\x02\xcf\x03\x00\x03'
    ',\x03S\x03v\x03\x96\x03\xb4\x03\xcf\x03\xe9\x04\x00\x04\x17\x04,\x04@\x04'
    'S\x04e\x04v\x04\x87\x04\x96\x04\xa5\x04\xb4\x04\xc2\x04\xcf\x04\xdc\x04'
    '\xe9\x04\xf5\x05\x00\x05\x0c\x05\x17\x05"\x05,\x056\x05@\x05J\x05S\x05\\'
    '\x05e\x05n\x05v\x05~\x05\x87\x05\x8e\x05\x96\x05\x9e\x05\xa5\x05\xad\x05'
    '\xb4\x05\xbb\x05\xc2\x05\xc9\x05\xcf\x05\xd6\x05\xdc\x05\xe2\x05\xe9\x05'
    '\xef\x05\xf5\x05\xfb\x06\x00\x06\x06\x06\x0c\x06\x11\x06\x17\x06\x1c\x06"'
    '\x06\'\x06,\x061\x066\x06;\x06@\x06E\x06J\x06N\x06S\x06X\x06\\\x06a\x06e'
    '\x06i\x06n\x06r\x06v\x06z\x06~\x06\x82\x06\x87\x06\x8b\x06\x8e\x06\x92'
    '\x06\x96\x06\x9a\x06\x9e\x06\xa2\x06\xa5\x06\xa9\x06\xad\x06\xb0\x06\xb4'
    '\x06\xb7\x06\xbb\x06\xbe\x06\xc2\x06\xc5\x06\xc9\x06\xcc\x06\xcf\x06\xd2'
    '\x06\xd6\x06\xd9\x06\xdc\x06\xdf\x06\xe2\x06\xe6\x06\xe9\x06\xec\x06\xef'
    '\x06\xf2\x06\xf5\x06\xf8\x06\xfb\x06\xfe\x07\x00\x07\x03\x07\x06\x07\t'
    '\x07\x0c\x07\x0f\x07\x11\x07\x14\x07\x17\x07\x1a\x07\x1c\x07\x1f\x07"\x07'
    '$\x07\'\x07)\x07,\x07/\x071\x074\x076\x079\x07;\x07>\x07@\x07B\x07E\x07G'
    '\x07J\x07L\x07N\x07Q\x07S\x07U\x07X\x07Z\x07\\\x07^\x07a\x07c\x07e\x07g'
    '\x07i\x07k\x07n\x07p\x07r\x07t\x07v\x07x\x07z\x07|\x07~\x07\x80\x07\x82'
    '\x07\x85\x07\x87\x07\x89\x07\x8b\x07\x8d\x07\x8e\x07\x90\x07\x92\x07\x94'
    '\x07\x96\x07\x98\x07\x9a\x07\x9c\x07\x9e\x07\xa0\x07\xa2\x07\xa3\x07\xa5'
    '\x07\xa7\x07\xa9\x07\xab\x07\xad\x07\xae\x07\xb0\x07\xb2\x07\xb4\x07\xb6'
    '\x07\xb7\x07\xb9\x07\xbb\x07\xbd\x07\xbe\x07\xc0\x07\xc2\x07\xc3\x07\xc5'
    '\x07\xc7\x07\xc9\x07\xca\x07\xcc\x07\xce\x07\xcf\x07\xd1\x07\xd2\x07\xd4'
    '\x07\xd6\x07\xd7\x07\xd9\x07\xdb\x07\xdc\x07\xde\x07\xdf\x07\xe1\x07\xe2'
    '\x07\xe4\x07\xe6\x07\xe7\x07\xe9\x07\xea\x07\xec\x07\xed\x07\xef\x07\xf0'
    '\x07\xf2\x07\xf3\x07\xf5\x07\xf6\x07\xf8\x07\xf9\x07\xfb\x07\xfc\x07\xfe'
    '\x07\xff\x08\x00')


def log2_256_more(a):
  """Returns a nonnegative integer at least 256 * log2(a).

  TODO(pts): How close is this upper bound?

  Input: a is an integer >= 0.

  If a <= 256, then the result is accurate (smallest upper bound).
  """
  if not isinstance(a, (int, long)):
    raise TypeError
  if a < 0:
    raise ValueError
  if a <= 1:
    return 0
  if a < 256:
    return LOG2_256_MORE_TABLE[a]
  d = bit_count(a) - 8
  m = a >> d
  return LOG2_256_MORE_TABLE[m + (m << d != a)] + (d << 8)


def log_more(a, b):
  """Returns a nonnegative integer at least a * ln(b).

  Input: a and b are integers, b >= 0.

  If b == 2 and a < 10 ** 16, then the result is the smallest possible.
  (TODO(pts): Verify this claim, especially the 16.)

  For larger values of b, the returned value might be off by a factor of 1/256.
  (TODO(pts): Verify this claim, especially relating to math.log(2) / 256
  approximation.)
  """
  if not isinstance(a, (int, long)):
    raise TypeError
  if not isinstance(b, (int, long)):
    raise TypeError
  if b < 0:
    raise ValueError
  if a <= 0 or b == 1:
    return 0
  if b == 2:
    # TODO(pts): Do it with smaller numbers for small values of a.
    # TODO(pts): Add a similar formula for b == 4, b == 8 and b == 16.
    return int((a * 69314718055994531 + 99999999999999999) / 100000000000000000)

  # Maple evalf(log(2) / 256, 30): 0.00270760617406228636491106297445
  # return a * log2_256_more(b) / 256.0 * math.log(2)
  # TODO(pts): Be more accurate with a different algorithm.
  return (a * log2_256_more(b) * 27076062 + 9999999999) / 10000000000


# Same as:
# import math
# import struct
# LOG2_256_LESS_TABLE = [
#     int(256 / math.log(2) * math.log(a or 1) + .0001) for a in xrange(256)]
# print repr(struct.pack('>256H', *[
#     int(256 / math.log(2) * math.log(a or 1) + .0001) for a in xrange(256)]))
LOG2_256_LESS_TABLE = struct.unpack('>256H',
    '\x00\x00\x00\x00\x01\x00\x01\x95\x02\x00\x02R\x02\x95\x02\xce\x03\x00\x03'
    '+\x03R\x03u\x03\x95\x03\xb3\x03\xce\x03\xe8\x04\x00\x04\x16\x04+\x04?\x04'
    'R\x04d\x04u\x04\x86\x04\x95\x04\xa4\x04\xb3\x04\xc1\x04\xce\x04\xdb\x04'
    '\xe8\x04\xf4\x05\x00\x05\x0b\x05\x16\x05!\x05+\x055\x05?\x05I\x05R\x05['
    '\x05d\x05m\x05u\x05}\x05\x86\x05\x8d\x05\x95\x05\x9d\x05\xa4\x05\xac\x05'
    '\xb3\x05\xba\x05\xc1\x05\xc8\x05\xce\x05\xd5\x05\xdb\x05\xe1\x05\xe8\x05'
    '\xee\x05\xf4\x05\xfa\x06\x00\x06\x05\x06\x0b\x06\x10\x06\x16\x06\x1b\x06!'
    '\x06&\x06+\x060\x065\x06:\x06?\x06D\x06I\x06M\x06R\x06W\x06[\x06`\x06d'
    '\x06h\x06m\x06q\x06u\x06y\x06}\x06\x81\x06\x86\x06\x8a\x06\x8d\x06\x91'
    '\x06\x95\x06\x99\x06\x9d\x06\xa1\x06\xa4\x06\xa8\x06\xac\x06\xaf\x06\xb3'
    '\x06\xb6\x06\xba\x06\xbd\x06\xc1\x06\xc4\x06\xc8\x06\xcb\x06\xce\x06\xd1'
    '\x06\xd5\x06\xd8\x06\xdb\x06\xde\x06\xe1\x06\xe5\x06\xe8\x06\xeb\x06\xee'
    '\x06\xf1\x06\xf4\x06\xf7\x06\xfa\x06\xfd\x07\x00\x07\x02\x07\x05\x07\x08'
    '\x07\x0b\x07\x0e\x07\x10\x07\x13\x07\x16\x07\x19\x07\x1b\x07\x1e\x07!\x07'
    '#\x07&\x07(\x07+\x07.\x070\x073\x075\x078\x07:\x07=\x07?\x07A\x07D\x07F'
    '\x07I\x07K\x07M\x07P\x07R\x07T\x07W\x07Y\x07[\x07]\x07`\x07b\x07d\x07f'
    '\x07h\x07j\x07m\x07o\x07q\x07s\x07u\x07w\x07y\x07{\x07}\x07\x7f\x07\x81'
    '\x07\x84\x07\x86\x07\x88\x07\x8a\x07\x8c\x07\x8d\x07\x8f\x07\x91\x07\x93'
    '\x07\x95\x07\x97\x07\x99\x07\x9b\x07\x9d\x07\x9f\x07\xa1\x07\xa2\x07\xa4'
    '\x07\xa6\x07\xa8\x07\xaa\x07\xac\x07\xad\x07\xaf\x07\xb1\x07\xb3\x07\xb5'
    '\x07\xb6\x07\xb8\x07\xba\x07\xbc\x07\xbd\x07\xbf\x07\xc1\x07\xc2\x07\xc4'
    '\x07\xc6\x07\xc8\x07\xc9\x07\xcb\x07\xcd\x07\xce\x07\xd0\x07\xd1\x07\xd3'
    '\x07\xd5\x07\xd6\x07\xd8\x07\xda\x07\xdb\x07\xdd\x07\xde\x07\xe0\x07\xe1'
    '\x07\xe3\x07\xe5\x07\xe6\x07\xe8\x07\xe9\x07\xeb\x07\xec\x07\xee\x07\xef'
    '\x07\xf1\x07\xf2\x07\xf4\x07\xf5\x07\xf7\x07\xf8\x07\xfa\x07\xfb\x07\xfd'
    '\x07\xfe')


def log2_256_less(a):
  """Returns a nonnegative integer at most 256 * log2(a).

  If a <= 256, then the result is accurate (largest lower bound).
  """
  if not isinstance(a, (int, long)):
    raise TypeError
  if a <= 0:
    raise ValueError
  if a < 256:
    return LOG2_256_LESS_TABLE[a]  # This is accurate.
  # The two assignments below are equivalent to:
  # d = 0
  # while a >= 256:
  #   a >>= 1
  #   d += 1
  d = bit_count(a) - 8
  a >>= d
  # assert 1 <= a <= 255  # True, but skipped for speed.
  # Equivalent to: return (d << 8) + int(256 / math.log(2) * math.log(a))
  return LOG2_256_LESS_TABLE[a] + (d << 8)


FIRST_PRIMES = (  # The first 54 primes, i.e. primes less than 256.
    '\x02\x03\x05\x07\x0b\r\x11\x13\x17\x1d\x1f%)+/5;=CGIOSYaegkmq\x7f\x83'
    '\x89\x8b\x95\x97\x9d\xa3\xa7\xad\xb3\xb5\xbf\xc1\xc5\xc7\xd3\xdf\xe3'
    '\xe5\xe9\xef\xf1\xfb')
FIRST_PRIMES_MAX = ord(FIRST_PRIMES[-1])


def prime_idx_more(i):
  """Returns a number equal or not much larger than the ith prime.

  Please note that the 1st prime is 2.

  Since the 664580th prime is 10000019, and prime_idx_more(664580) == 10641760,
  so at this range the returned value is about 6.42% larger than the real one.
  """
  #if i <= 2:
  #  return 2 + (i == 2)
  if i < len(FIRST_PRIMES):
    if i < 1:
      return 2
    # Don't use _prime_cache here, it would make the return value
    # nondeterministic.
    return ord(FIRST_PRIMES[i])

  # This also seems to work, but it saves only a little (10641712 from
  # 10641760) for large values, and its correctness is unproven.
  #if i > 35:
  #  i -= 4
  #elif i > 26:
  #  i -= 3
  #elif i > 17:
  #  i -= 2
  #elif i > 10:
  #  i -= 1

  # Make n be an integer at least n * (math.log(n) + math.log(math.log(n))),
  # as given by p_i <= i * ln(i) + i * ln(ln(i)) if i >= 6, based on
  # http://en.wikipedia.org/wiki/Prime-counting_function#Inequalities
  #
  # The formula also happens to be correct (manually verified) for i == 3,
  # i == 4 and i == 5. It's incorrect for i <= 2.
  return log_more(i, log_more(i, i))


# !! Test:
#ps = primes_upto(1000)
#print prime_idx_more(len(ps))
#for i1, p in enumerate(ps):
#  i = i1 + 1
#  pm = prime_idx_more(i)
#  if p > pm:
#    print (i, p, pm)


def first_primes_moremem(i):
  """Returns a list containing the first i primes.

  About 9.1% faster than yield_first_primes(i), but it uses about twice as
  much memory for a few primes which it will ignore soon.
  """
  if i <= len(FIRST_PRIMES):
    return map(ord, FIRST_PRIMES[:i])
  cache = _prime_cache
  if i <= len(cache):
    return cache[:i]

  s = primes_upto(prime_idx_more(i))
  del s[i:]
  return s


def first_primes(i):
  """Returns a list containing the first i primes.

  Faster than yield_first_primes(i), but it uses more memory.
  """
  if i <= len(FIRST_PRIMES):
    return map(ord, FIRST_PRIMES[:i])
  cache = _prime_cache
  if i <= len(cache):
    return cache[:i]
  n = prime_idx_more(i)
  # The rest is equivalent to this, but the rest saves memory by not creating
  # a long temporary list, and it's about 9.1% slower.
  #
  #   return primes_upto(n)[:i]
  n += 1
  s = A1 * (n >> 1)
  a0 = A0
  for j in xrange(3, sqrt_floor(n) + 1, 2):
    if s[j >> 1]:
      ii = j * j
      s[ii >> 1 : : j] = a0 * ((((n - ii - 1) / j) >> 1) + 1)
  t = []
  for j in xrange(n >> 1):  # This is the slow loop.
    if s[j]:
      t.append((j << 1) | 1)
      if len(t) == i:
        t[0] = 2  # Change from 1.
        return t
  assert 0, 'Too few primes: i=%d n=%d len(t)=%d' % (i, n, len(t))


def gcd(a, b):
  """Returns the greatest common divisor of integers a and b.

  If both a and b are 0, then it returns 0.

  Similar to fractions.gcd, but works for negatives as well.
  """
  if a < 0:
    a = -a
  if b < 0:
    b = -b
  while b:
    a, b = b, a % b
  return a


def fraction_to_float(a, b):
  """Converts the integer fraction a / b to a nearby float.

  This works even if float(a) and float(b) are too large.

  Please note that there may be a loss of precision because of the float
  return value.

  This works even in Python 2.4.

  Raises:
    ZeroDivisionError: If b == 0.
    OverflowError: If the result cannot be represented as a float.
  """
  # TODO(pts): Would this make it work faster?
  #   g = gcd(a, b)
  #   if g > 1:
  #     a /= g
  #     b /= g
  #
  # Smart implementation details in long_true_divide in Objects/longobject.c.
  return a.__truediv__(b)


def prime_index(n, limit=256):
  """Returns the index of n in the prime list if n is prime, otherwise None.

  Builds an in-memory prime cache for all primes up to n (and maybe a bit
  beyond).

  Args:
    n: A nonnegative integer.
    limit: Minimum number of prime cache size to build if needed.
  Returns:
    The index of n in the prime list, or None if n is not a prime. For example:
    prime_index(2) == 0, prime_index(3) == 1, prime_index(4) == None,
    prime_index(5) == 3.
  """
  if n > _prime_cache_limit_ary[0]:
    while limit < n:
      limit <<= 1
    ensure_prime_cache_upto(limit)
  cache = _prime_cache
  i = bisect.bisect_left(cache, n)
  if i >= len(cache) or cache[i] != n:
    return None  # n is not a prime.
  return i


def prime_count_cached(n, limit=256):
  """Returns the number of primes at most n.

  This is pi(n), the prime-counting function:
  http://en.wikipedia.org/wiki/Prime-counting_function

  Builds an in-memory prime cache for all primes up to n (and maybe a bit
  beyond).

  Args:
    n: A nonnegative integer.
    limit: Minimum number of prime cache size to build if needed.
  Returns:
    The number of primes p for which 2 <= p <= n. For example:
    prime_count(0) == 0, prime_count(1) == 0, prime_count(2) == 1,
    prime_count(3) == 2, prime_count(4) == 2, prime_count(5) == 3.
  """
  if n > _prime_cache_limit_ary[0]:
    while limit < n:
      limit <<= 1
    _prime_cache[:] = primes_upto(limit)
    # For thread safety and for good _prime_cache interaction between
    # primes_upto and prime_index, set this after updating _prime_cache.
    _prime_cache_limit_ary[0] = limit
  return bisect.bisect_right(_prime_cache, n)


PRIME_COUNTS_STR_127 = (
    '\0\0\1\2\2\3\3\4\4\4\4\5\5\6\6\6\6\7\7\10\10\10\10\t\t\t\t\t'
    '\t\n\n\x0b\x0b\x0b\x0b\x0b\x0b\x0c\x0c\x0c\x0c\r\r\x0e\x0e\x0e'
    '\x0e\x0f\x0f\x0f\x0f\x0f\x0f\x10\x10\x10\x10\x10\x10\x11\x11'
    '\x12\x12\x12\x12\x12\x12\x13\x13\x13\x13\x14\x14\x15\x15\x15'
    '\x15\x15\x15\x16\x16\x16\x16\x17\x17\x17\x17\x17\x17\x18\x18'
    '\x18\x18\x18\x18\x18\x18\x19\x19\x19\x19\x1a\x1a\x1b\x1b\x1b'
    '\x1b\x1c\x1c\x1d\x1d\x1d\x1d\36\36\36\36\36\36\36\36\36\36\36'
    '\36\36\36')


def prime_count_more(n, accuracy=100000):
  """Returns an integer which is at least the number of primes up to n.

  Please note that although prime_count(n) is increasing as n increases,
  this function in't. A large decrease (e.g. 39) between consecutive
  return values is possible because of rounding errors.

  Args:
    n: An integer, upper limit, count these primes p: 2 <= p <= n.
    accuracy: An upper limit on how much larger the result is allowed to be
      relatively: prime_count_more(n, accuracy) * 10 ** 6 < prime_count(n) *
      (10 ** 6 + accuracy) is always true for n > 1 (and it's equal for
      n <= 1). Please note that the minimum allowed accuracy is currently 3000.
  Returns:
    An upper bound of the number of primes p in: 2 <= p <= n. prime_count(n)
    <= prime_count_more(n) is always true.
  """
  if not isinstance(n, (int, long)):
    raise TypeError
  if not isinstance(accuracy, (int, long)):
    raise TypeError
  if accuracy < 3000:
    raise ValueError('Desired accuracy must be >= 3000, got: %r' % (accuracy,))

  if n < 0:
    return 0  # Accurate.
  if n < 127:  # Accurate value from lookup table.
    return ord(PRIME_COUNTS_STR_127[n])
  if (accuracy >= 100000 or n > 302976 or (accuracy >= 50000 and n > 546) or
      (accuracy >= 10000 and n > 11775) or (accuracy >= 5000 and n > 48382) or
      (accuracy >= 4000 and n > 70143)
      # or (accuracy >= 3000 and n > 302976)  # This last one is implied.
     ):
    # The value returned below is >= prime_count(n) for n >= 4, and it's at
    # most 10% larger than prime_count(n) for n >= 101, and it's less than
    # 10% larger than prime_count(n) for n >= 127.
    #
    # Proof of the upper bound for n > 60184: It computes an upper bound of
    # n / (math.log(n) - 1.1)
    # accurately, based on the theorem by Pierre Dusart
    # (http://en.wikipedia.org/wiki/Prime-counting_function#Inequalities),
    # assuming that floating point arithmetic is correct.
    #
    # The conditions for accuracy above were verified empirically, for n up to
    # 10 ** 7.
    v = int(n * 5540 / (log2_256_less(n) * 15 - 6094))
    if 24107 <= n <= 60174:
      v += 3  # `v += 1' and `v += 2' would have been enough in some cases.
    return v

  # n is too small, we have to compute accurately.
  if n <= _prime_cache_limit_ary[0]:
    return bisect.bisect_right(_prime_cache, n)
  if accuracy >= 50000:
    limit = 546
  elif accuracy >= 10000:
    limit = 11775
  elif accuracy >= 5000:
    limit = 48382
  elif accuracy >= 4000:
    limit = 70143
  elif accuracy >= 3000:
    limit = 302076
  else:
    assert 0, 'Cannot compute limit for accuracy=%d' % accuracy
  return prime_count(n, limit)


def is_prime(n, accuracy=None):
  """Returns bool indicating whether the integer n is probably a prime.

  Uses the deterministic Rabin-Miller primality test if accuracy is None, and
  a probabilistic version (with a fixed set of ``pseudo-random'' primes) of
  the same test if accuracy is an integer. Uses an optimized (i.e. small) list
  of bases for the deterministic case if n <= 1 << 64.

  Please note that the correctness of the deterministic Rabin-Miller
  primality test depends on the validity of the generalized Riemann
  hypothesis for quadratic Dirichlet characters. This has not been proven
  yet. This affects us when n > 1 << 64 and accuracy is None are both true.

  Args:
    n: The integer whose primality is to be tested.
    accuracy: None for absolutely sure results or a nonnegative integer
      describing the desired accuracy (see more in the `Returns:' section).
      Please note that accuracy is ignored (i.e. assumed to be None) if n <=
      1 << 64. So the result for small values of n is always correct. If
      accuracy <= 7, then 7 is used instead.
  Returns:
    False if n is composite or -1 <= n <= 1; True if n is a prime; 1 if n is a
    prime with probability at least 1 - 4.0 ** -accuracy. If accuracy is None
    or n <= 1 << 64, then `1' is never returned, i.e. the result is always
    correct.
  """
  if n < 2:
    if n > -2:
      return False
    n = -n
  if not (n & 1):
    return n == 2  # n == 2 is prime, other even numbers are composite.
  is_accurate = True
  # Using the _prime_cache for small n (n < 10 ** 5) brings a 3.69 times
  # speedup. For large values of n it will bring even more.
  if n <= _prime_cache_limit_ary[0]:
    cache = _prime_cache
    i = bisect.bisect_left(cache, n)
    return i < len(cache) and cache[i] == n
  # These bases were published on http://miller-rabin.appspot.com/ . Suboptimal
  # (i.e. containing more bases) base lists are also at
  # http://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test#Deterministic_variants_of_the_test
  if n < 1373653:
    if n == 3:
      return True  # n == 3 is prime.
    bases = (2, 3)
  elif n < 316349281:
    # 11000544 == 2**5 * 3 * 19 * 37 * 163
    # 31481107 == 7 * 241 * 18661
    # This is already checked above, so early return is not needed.
    # if n in (3, 7, 19, 37, 163, 241, 18661):
    #   return True
    bases = (11000544, 31481107)
  elif n < 105936894253:
    # 1005905886 == 2 * 3 * 113 * 1483637
    # 1340600841 == 3**3 * 17 * 19 * 347 * 443
    # 1483637 < 316349281, so early return is not needed.
    bases = (2, 1005905886, 1340600841)
  elif n < 31858317218647:
    # 3046413974 < 105936894253, so early return is not needed.
    bases = (2, 642735, 553174392, 3046413974)
  elif n < 3071837692357849:
    # 3613982119 < 31858317218647, so early return is not needed.
    bases = (2, 75088, 642735, 203659041, 3613982119)
  elif n < 18446744073709551617:  # About (1 << 64).
    # 1795265022 < 3071837692357849, so early return is not needed.
    bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
  elif accuracy is None:
    # According to
    # http://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test#Deterministic_variants_of_the_test
    # it is enough to go up to min(n - 1, 2 * math.log(n) ** 2), but
    # the 2nd part of the min is already smaller when n >= 18. The 2nd part of
    # the min is 178 for n == (1 << 64 | 1). That's a steep slowdown from the
    # at most 7 elements in bases for smaller values of n.
    #
    # Please note that this test categorizes n == 5 and n == 7 as primes, but
    # we have better tests above for such smaller numbers.
    #
    # Please note that the correctness of this tests depends on the validity
    # of the generalized Riemann hypothesis for quadratic Dirichlet
    # characters. This has not been proven yet.
    # TODO(pts): Check this.
    bases = xrange(2, 1 + (log_more(log_more(65536, n), n) >> 15))
  else:
    is_accurate = False
    if accuracy <= len(FIRST_PRIMES):  # 54.
      bases = map(ord, FIRST_PRIMES[:max(7, accuracy)])
    else:
      bases = first_primes_moremem(accuracy)

  n1 = n - 1
  #: assert n1 > 1
  s = 0
  while not (n1 & (1 << s)):
    s += 1
  if s:
    h = (1, n1)
    n2 = n1 >> s
    for b in bases:
      a = pow(b, n2, n)
      if a not in h:
        a = (a * a) % n
        for _ in xrange(s - 1):
          if a in h:
            break
          a = (a * a) % n
        if a != n1:
          return False  # n is composite.
  if is_accurate:
    return True  # n is a prime.
  return 1  # n is probably prime: P(n is prime) >= 1 - 4.0 ** -accuracy.


def next_prime(n):
  """Returns the smallest positive prime larger than n."""
  if n <= 1:
    return 2
  elif n < FIRST_PRIMES_MAX:
    return ord(FIRST_PRIMES[bisect.bisect_right(FIRST_PRIMES, chr(n))])
  else:
    n += 1 + (n & 1)
    k = n % 6
    if k == 3:
      n += 2
    if is_prime(n):
      return n
    if k != 1:
      n += 2
      if is_prime(n):
        return n
    n += 4
    # This below is the same as the end of nextprime() sympy-0.7.2. There is
    # no such function in pycrypto.
    while 1:
      if is_prime(n):
        return n
      n += 2
      if is_prime(n):
        return n
      n += 4

#ps = primes_upto(100000)
#i = 0
#for x in xrange(-42, 100001):
#  if x == ps[i]:
#    i += 1
#    if i == len(ps):
#      break
#  y = next_prime(x)
#  assert y == ps[i], (ps[i], y, x)


def choose(n, k):
  """Returns the binomial coefficient n choose k."""
  if not isinstance(n, (int, long)):
    raise TypeError
  if not isinstance(k, (int, long)):
    raise TypeError
  if n < 0:
    raise ValueError
  if k < 0 or k > n:
    return 0
  if k > n >> 1:
    k = n - k
  if k:
    c = 1
    n += 1
    for i in xrange(1, k + 1):
      c = c * (n - i) / i
    return c
  else:
    return 1


def yield_slow_factorize(n):
  """Yields an increasing list of prime factors whose product is n.

  The implementation is slow because it uses trial division. Please use
  factorize instead, which is fast.

  Among the factorization algorithms using trial division, this implementation is
  pretty fast.
  """
  if n <= 0:
    raise ValueError
  s = 0
  while not (n & (1 << s)):
    yield 2
    s += 1
  n >>= s
  while not (n % 3):
    yield 3
    n /= 3
  d = 5
  q = sqrt_floor(n)
  # We have quite a bit of code repetition below just so that we can have
  # d += 4 every second time instead of d += 2.
  while d <= q:
    if not (n % d):
      yield d
      n /= d
      while not (n % d):
        yield d
        n /= d
      q = sqrt_floor(n)
    d += 2
    if d > q:
      break
    if not (n % d):
      yield d
      n /= d
      while not (n % d):
        yield d
        n /= d
      q = sqrt_floor(n)
    d += 4
  if n > 1:
    yield n


def divisor_count(n):
  if n <= 0:
    raise ValueError
  q = 0
  e = 0
  c = 1
  for p in factorize(n):
    if p == q:
      e += 1
    else:
      c *= e + 1
      q = p
      e = 1
  return c * (e + 1)


def rle(seq):
  """Does run-length encoding.

  E.g. transforms 'foo' ,'bar', 'bar', 'baz'...
  to ('foo', 1), ('bar', 2), ('baz', 1), ...
  """
  prev = count = 0  # The value of prev is arbitrary here.
  for x in seq:
    if not count:
      prev = x
      count = 1
    elif prev == x:
      count += 1
    else:
      yield prev, count
      prev = x
      count = 1
  if count:
    yield prev, count


def divisor_sum(n):
  """Returns the sum of positive integer divisors of n (including 1 and n)."""
  if not isinstance(n, (list, tuple)):
    if not isinstance(n, (int, long)):
      raise TypeError
    if n <= 0:
      raise ValueError
    n = factorize(n)
  s = 1
  for prime, exp in rle(n):
    s *= (prime ** (exp + 1) - 1) / (prime - 1)
  return s


def simplify_nonneg(a, b):
  """Simplifies the nonnegative rational a / b. Returns (aa, bb)."""
  x, y = a, b
  while y:  # Calculate the GCD.
    x, y = y, x % y
  return a / x, b / x


class MiniIntRandom(_random.Random):
  """Class which can generate random integers, without using floating point.

  Uses Python's built-in Mersenne twister (MT19937).

  Constructor arguments: Pass an integer to specify the seed, or omit to use
  the current time as seed.
  """
  cached_bit_count = (None, None)

  def randrange(self, start, stop):
    """Returns a random integer in the range: start <= retval < stop."""
    n = stop - start
    if n <= 0:
      raise ValueError
    # TODO(pts): Measure the speed of this method vs random.Random.randrange.
    # Caching the result of bit_count(n), because bit counting can be
    # potentially slow.
    # TODO(pts): Measure the speed of caching.
    # TODO(pts): Measure how the random number generation speed affects the
    # factorization speed.
    cc, cn = self.cached_bit_count
    if cn == n:
      c = cc
    else:
      c = bit_count(n)
      self.cached_bit_count = (c, n)
    # TODO(pts): Come up with something faster.
    r = self.getrandbits(c)
    while r >= n:
      r = self.getrandbits(c)
    return r + start


def pollard(n, random_obj):
  """Try to find a non-trivial divisor of n using Pollard's Rho algorithm.

  This is similar but slower than brent(...). Please use brent(...) instead.

  This implementation is based on a merge of
  http://comeoncodeon.wordpress.com/2010/09/18/pollard-rho-brent-integer-factorization/
  and http://code.activestate.com/recipes/577037-pollard-rho-prime-factorization/
  , but several bugs were fixed.

  pycrypto doesn't contain code for integer factorization.
  SymPy (sympy/ntheory/factor_.py) contains Pollard Rho and Pollard p-1.

  Args:
    n: An integer >= 2 to find a non-trivial divisor of.
    random_obj: An object which can generate random numbers using the
      .randrange method (see Random.randrange for documentation); or None to
      create a default one using n as the seed. .randrange may be called several
      times, which modifies random_obj's internal state.
  Returns:
    For prime n: returns n quite slowly.

    For composite n: usually 2 <= retval < n and n % retval == 0; but sometimes
    retval == n, so no non-trivial divisors could be found.

    May return n even for small composite numbers (e.g. 9, 15, 21, 25, 27).
  """
  if n <= 1:
    raise ValueError
  if not (n & 1):
    return 2
  # Calling random_obj.randrange with the same argument to take advantage of
  # the bit count caching in MiniIntRandom.
  y = random_obj.randrange(1, n)
  c = random_obj.randrange(1, n)
  while c == n - 2:  # -2 is a bad choice for c.
    c = random_obj.randrange(1, n)
  x = y
  g = 1
  while g == 1:
    x = (x * x + c) % n
    y = (y * y + c) % n
    y = (y * y + c) % n
    g = gcd(abs(x - y), n)
    if g == n:
      break  # Failed, try again with a different c.
  return g


def brent(n, random_obj):
  """Try to find a non-trivial divisor of n using Brent's algorithm.

  This is similar but faster than pollard(...).

  This implementation is based on the merge of
  http://comeoncodeon.wordpress.com/2010/09/18/pollard-rho-brent-integer-factorization/
  and http://mail.python.org/pipermail/python-list/2009-November/559592.html and
  http://code.activestate.com/recipes/577037-pollard-rho-prime-factorization/ and
  http://forums.xkcd.com/viewtopic.php?f=11&t=97639
  , but several bugs were fixed and several speed improvements were made.

  pycrypto doesn't contain code for integer factorization. SymPy doesn't
  contain Brent's method.

  Args:
    n: An integer >= 2 to find a non-trivial divisor of.
    random_obj: An object which can generate random numbers using the
      .randrange method (see Random.randrange for documentation); or None to
      create a default one using n as the seed. .randrange may be called several
      times, which modifies random_obj's internal state.
  Returns:
    For prime n: returns n quite slowly.

    For composite n: usually 2 <= retval < n and n % retval == 0; but sometimes
    retval == n, so no non-trivial divisors could be found.

    May return n even for small composite numbers (e.g. 9, 15, 21, 25, 27).
  """
  if n <= 1:
    raise ValueError
  if not (n & 1):
    return 2
  # Calling random_obj.randrange with the same argument to take advantage of
  # the bit count caching in MiniIntRandom.
  y = random_obj.randrange(1, n)
  c = random_obj.randrange(1, n)
  while c == n - 2:  # -2 is a bad choice for c.
    c = random_obj.randrange(1, n)
  if c == n - 2:  # -2 is a bad choice for c.
    c = n - 1
  m = random_obj.randrange(1, n)
  g = r = q = 1
  while g == 1:
    x = y
    for i in xrange(r):
      # Some implementations use `y = (pow(y, 2, n) + c) % n' instead, but that's
      # about 3.65 times slower.
      y = (y * y + c) % n
    k = 0
    while k < r and g == 1:  # Always true in the beginning.
      ys = y
      for i in xrange(min(m, r - k)):
        # Assigning to y and q in parallel here (and at PA2 below) would
        # change the algorithm, but it appears that factorization using that
        # still produces correct result, but it is about 4.5% slower.
        y = (y * y + c) % n
        q = (q * abs(x - y)) % n
      g = gcd(q, n)
      k += m
    r <<= 1
  if g == n:
    while 1:
      ys = (ys * ys + c) % n  # PA2: ys, g = ...
      g = gcd(abs(x - ys), n)
      if g > 1:
        break  # At this point we may still return n.
  return int(g)


def finder_slow_factorize(n, divisor_finder=None, random_obj=None):
  """Factorize a number recursively, by finding divisors.

  This function is slow. Please use factorize(...) instead.

  This function is slow because it doesn't propagate prime divisors of d to
  n / d; and it also doesn't use trial divison to find small prime divisors
  quickly.

  Factorization uses pseudorandom numbers, but it's completely deterministic,
  because the random seed depends only on the arguments (n and random_obj).

  Args:
    n: Positive integer to factorize.
    divisor_finder: A function which takes a positive composite integer k and
      random_obj. Always returns k or a non-trivial divisor of k. Can use
      random. Not called for prime numbers. If None is passed, then a
      reasonable fast default is used (currently brent(...)).
    random_obj: An object which can generate random numbers using the
      .randrange method (see Random.randrange for documentation); or None to
      create a default one using n as the seed. .randrange may be called several
      times, which modifies random_obj's internal state.
  Returns:
    List of prime factors (with multiplicity), in increasing order.
  """
  if n < 1:
    raise ValueError
  if n == 1:
    return []
  if divisor_finder is None:
    divisor_finder = brent
  if random_obj is None:
    random_obj = MiniIntRandom(n)
  numbers_to_factorize = [n]
  ps = []  # Prime factors found so far (with multiplicity).
  while numbers_to_factorize:
    n = numbers_to_factorize.pop()
    while not is_prime(n):
      d = divisor_finder(n, random_obj)
      while d == n:  # Couldn't find a non-trivial divisor.
        d = divisor_finder(n, random_obj)  # Try again.
      numbers_to_factorize.append(d)
      n /= d
    ps.append(n)
  ps.sort()
  return ps


# Empty or contains primes 3, 5, ..., <= _SMALL_PRIME_LIMIT.
_small_primes_for_factorize = []

#def _compute_small_primes_for_factorize():
#  assert not small_primes_for_factorize
#  small_primes_for_factorize[:] = primes_upto(65536)

_SMALL_PRIME_LIMIT = 65536
# The larger `nextprime(_SMALL_PRIME_LIMIT) ** 2' would also work.
_SMALL_PRIME_CUTOFF = (_SMALL_PRIME_LIMIT + 1) ** 2


def factorize(n, divisor_finder=None, random_obj=None):
  """Returns an increasing list of prime factors whose product is n.

  All primes which fit to an int are added as an int (rather than a long).

  Factorization uses pseudorandom numbers, but it's completely deterministic,
  because the random seed depends only on the arguments (n and random_obj).

  This algorithm is not the fastest known integer factorization algorithm,
  but it represents a reasonable balance between speed and complexity. For a
  more complex, but faster method, see
  http://sourceforge.net/projects/pyecm/ , but for small numbers (< 10 **
  33) that's still faster than this algorithm. Pyecm uses Elliptic curve
  factorization method (ECM), which is the third-fastest known factoring method.
  The second fastest is the multiple polynomial quadratic sieve and the
  fastest is the general number field sieve.

  Args:
    n: Positive integer to factorize.
    divisor_finder: A function which takes a positive composite integer k and
      random_obj. Always returns k or a non-trivial divisor of k. Can use
      random. Not called for prime numbers. If None is passed, then a
      reasonable fast default is used (currently brent(...)).
    random_obj: An object which can generate random numbers using the
      .randrange method (see Random.randrange for documentation); or None to
      create a default one using n as the seed. .randrange may be called several
      times, which modifies random_obj's internal state.
  Returns:
    List of prime factors (with multiplicity), in increasing order.
  """
  if n <= 0:
    raise ValueError
  if n == 1:
    return []
  if is_prime(n):
    return [n]
  # We will extend ps with all prime factors of n (with multiplicity).
  # We will extend pds with all prime factors of n (each prime once).
  # We extend with int instead of long if the number fits in an int.
  ps = []
  pds = []

  # Trial division for small primes.

  if not _small_primes_for_factorize:
    # TODO(pts): Adjust _SMALL_PRIME_LIMIT.
    #
    # Depending on _SMALL_PRIME_LINIT, we have:
    #   1000:  168 primes,  p == 1/12.3509756739 == 0.0809652635068
    #   65536: 6542 primes, p == 1/19.7576704153 == 0.0506132544466
    #
    # p is the probability that we can't factorize n trying only
    # _small_primes_for_factorize (because n has only larger prime divisors
    # than _SMALL_PRIME_LIMIT).
    #
    # p was computed using:
    #
    #   a = b = 1
    #   for p in primes_upto(_SMALL_PRIME_LIMIT):
    #     a *= p - 1
    #     b *= p
    #   p = fraction_to_float(a, b)

    # This is thread-safe because of the global interpreter lock.
    _small_primes_for_factorize[:] = primes_upto(_SMALL_PRIME_LIMIT)[1:]
  q = sqrt_floor(n)
  if q >= 2 and not (n & 1):
    pds.append(2)
    ps.append(2)
    p = 1
    while not (n & (1 << p)):
      p += 1
      ps.append(2)
    n >>= p
    q = sqrt_floor(n)
  for p in _small_primes_for_factorize:
    if p > q:
      break
    if not (n % p):
      pds.append(p)
      ps.append(p)
      n /= p
      while not (n % p):
        ps.append(p)
        n /= p
      q = sqrt_floor(n)
  n = int(n)  # This is fast: O(1) for int and long.
  if n == 1:
    ps.sort()
    return ps
  if n < _SMALL_PRIME_CUTOFF:
    ps.append(n)  # n is prime, because we've tried all its prime divisors.
    ps.sort()
    return ps

  # Now n doesn't have any small divisors, so we continue with Brent's
  # algorithm (or the slower Pollard's Rho algorithm, if configured so) to
  # find a non-trivial divisor d. Since d is not necessarily a prime, we
  # recursively factorize d and n / d until we find primes. The implementation
  # below is a bit tricky, because it uses a stack instead of recursion to
  # avoid the Python stack overflow, and it also propagates prime divisors from
  # d to n / d, i.e. if it finds that p is a prime divisor of d, and then it
  # will try p first (i.e. before another call to Brent's algorithm) when
  # factorizing n / d.

  if divisor_finder is None:
    divisor_finder = brent
  if random_obj is None:
    random_obj = MiniIntRandom(n)
  stack = [(int(n), len(pds))]
  while stack:
    n, i = stack.pop()

    # Propagate prime divisors from d to n / d.
    #
    # It's not true that this time i starts where the last time this loop
    # finished. In fact, i may start earlier. So we have to keep the i values
    # in the stack.
    for i in xrange(i, len(pds)):
      p = int(pds[i])
      while not (n % p):
        ps.append(p)
        n /= p

    # True: assert gcd(product(ps), n) == 1.
    if n == 1:
      continue
    n = int(n)  # This is fast: O(1) for int and long.
    while 1:
      if n < _SMALL_PRIME_CUTOFF or is_prime(n):  # n is prime.
        ps.append(n)
        pds.append(n)
        break
      d = divisor_finder(n, random_obj)
      while d == n:
        d = divisor_finder(n, random_obj) # Retry with different random numbers.
      # True: assert 1 < d < n and n % d == 0
      n /= d
      n = int(n)
      d = int(d)
      # True: assert n > 1 and d > 1
      if d > n:
        stack.append((d, len(pds)))
      else:
        stack.append((n, len(pds)))
        n = d
  ps.sort()
  return ps


def totient(n):
  """Returns the Euler totient of a nonnegative integer.

  http://en.wikipedia.org/wiki/Euler%27s_totient_function

  Args:
    n: Integer >= 0.
  """
  if n == 0:
    return 0
  result = 1
  for p, a in rle(factorize(n)):
    result *= p ** (a - 1) * (p - 1)
  return result


def totients_upto(limit, force_recursive=False):
  """Computes the Euler totient of nonnegative integers up to limit.

  http://en.wikipedia.org/wiki/Euler%27s_totient_function

  Args:
    limit: Integer >= 0.
    force_recursive: bool indicating whether the recursive implementation
      should be forced.
  Returns:
    A list of length `limit + 1', whose value at index i is totient(i).
  """
  if limit <= 1:
    if limit < 0:
      raise ValueError
    if limit:
      return [0, 1]
    else:
      return [0]
  if not force_recursive and limit <= 1800000:
    # For small values, _totients_upto_iterative is faster. _totients_upto_iter
    # also uses double memory, so let's not use it for large values.
    return _totients_upto_iterative(limit)
  primes = primes_upto(limit)
  primec = len(primes)
  result = [None] * (limit + 1)
  result[0] = 0
  result[1] = 1

  def generate(i, n, t):  # Populates `result'.
    #print 'generate(i=%d, n=%d, t=%d, p=%d)' % (i, n, t, primes[i])
    while 1:
      p = primes[i]
      i += 1
      n0, t0 = n, t
      n *= p
      t *= p - 1
      while n <= limit:
        # assert result[n] is None  # True but speed.
        result[n] = t
        if i < primec:
          generate(i, n, t)
        n *= p
        t *= p
      n, t = n0, t0
      if i >= primec or n * primes[i] > limit:
        break

  generate(0, 1, 1)
  # assert not [1 for x in result if x is None]  # True but speed.
  return result


def _totients_upto_iterative(limit):
  """Like totients_upto, but iterative, and uses more memory.

  Input: limit is an integer >= 1.
  """
  ns = [1]
  result = [None] * (limit + 1)
  result[0] = 0
  result[1] = 1
  limit_sqrt = sqrt_floor(limit) + 1
  primes = primes_upto(limit)
  limit_idx2 = 0
  for p in primes:
    if p > limit_sqrt:  # No sorting anymore.
      t = p - 1
      for i in xrange(limit_idx2):
        n = ns[i]
        pan = p * n
        if pan > limit:
          break
        #assert result[pan] is None, (p, n, pan)  # True but speed.
        result[pan] = result[n] * t
      continue
    ns.sort()  # Fast sort, because of lots of increasing runs.
    pa = p
    ta = p - 1
    limit_idx = len(ns)
    while pa <= limit:
      ns.append(pa)
      result[pa] = ta
      for i in xrange(1, limit_idx):
        n = ns[i]
        pan = pa * n
        if pan > limit:
          break
        ns.append(pan)
        result[pan] = ta * result[n]
      pa *= p
      ta *= p
    limit_idx2 = len(ns)
  return result


def yield_totients_upto(limit):
  """Yields Euler totients up to a limit.

  Faster than ((i, totient(i)) for i in xrange(1, 1 + limit)).

  Uses a bit less memory than totients_upto, but it still generates
  primes_upto(limit).

  http://en.wikipedia.org/wiki/Euler%27s_totient_function

  Args:
    limit: Integer >= 1.
  Yields:
    (i, totient(n)) pairs for all i (1 <= n <= limit), in undefined order.
  """
  yield (1, 1)
  if limit > 1:
    primes = primes_upto(limit)
    primec = len(primes)

    def generate(i, n, t):
      while 1:
        p = primes[i]
        i += 1
        n0, t0 = n, t
        n *= p
        t *= p - 1
        while n <= limit:
          yield (n, t)
          if i < primec:
            for r in generate(i, n, t):
              yield r
          n *= p
          t *= p
        n, t = n0, t0
        if i >= primec or n * primes[i] > limit:
          break

    for r in generate(0, 1, 1):
      yield r


def yield_factorize_upto(limit):
  """Yields numbers with their factorization up to a limit.

  Faster than ((i, factorize(i)) for i in xrange(1, 1 + limit)).

  Args:
    limit: Integer >= 1.
  Yields:
    (i, factorize(i)) pairs for all i (1 <= n <= limit), in undefined order.
  """
  if limit < 1:
    raise ValueError
  yield (1, [])
  if limit > 1:
    primes = primes_upto(limit)
    primec = len(primes)

    def generate(i, n, t):  # Doesn't modify t.
      while 1:
        p = primes[i]
        i += 1
        n0, t0 = n, t
        n *= p
        t = t + [p]
        while n <= limit:
          yield (n, t[:])
          if i < primec:
            for r in generate(i, n, t):
              yield r
          n *= p
          t.append(p)
        n, t = n0, t0
        if i >= primec or n * primes[i] > limit:
          break

    for r in generate(0, 1, []):
      yield r


def divisor_counts_upto(limit, result=None):
  """Computes the number of divisors of nonnegative integers up to limit.

  Args:
    limit: Integer >= 0.
    result: Optional list (or array) to save the resulting value to. If None,
      a new list of the right size (limit + 1) will be created.
  Returns:
    A list of length `limit + 1', whose value at index i is the number of
    positive integers who divide i. At index 0, 0 is returned.
  """
  if limit <= 1:
    if limit:
      return [0, 1]
    else:
      return [0]
  primes = primes_upto(limit)
  primec = len(primes)
  if result is None:
    result = [None] * (limit + 1)
  else:
    assert len(result) == limit + 1
  result[0] = 0
  result[1] = 1

  def generate(i, n, t):  # Populates `result'.
    #print 'generate(i=%d, n=%d, t=%d, p=%d)' % (i, n, t, primes[i])
    while 1:
      p = primes[i]
      i += 1
      n0, t0 = n, t
      n *= p
      t += t0
      while n <= limit:
        # assert result[n] is None  # True but speed.
        result[n] = t
        if i < primec:
          generate(i, n, t)
        n *= p
        t += t0
      n, t = n0, t0
      if i >= primec or n * primes[i] > limit:
        break

  generate(0, 1, 1)
  # assert not [1 for x in result if x is None]  # True but speed.
  return result


def yield_divisors_unsorted(n):
  """Yields the positive divisors of n, in any order."""
  if isinstance(n, (list, tuple)):
    pas = n
  else:
    pas = n > 1 and tuple(rle(factorize(n)))

  def generate(i):
    p, a = pas[i]
    pps = [1]
    while a >= len(pps):
      pps.append(pps[-1] * p)
    if i:
      for d in generate(i - 1):
        for pp in pps:
          yield d * pp
    else:
      for pp in pps:
        yield pp

  if pas:
    for d in generate(len(pas) - 1):
      yield d
  else:
    yield 1


def divisors(n):
  """Returns the list of positive divisors of n in increasing order."""
  ds = list(yield_divisors_unsorted(n))
  ds.sort()
  return ds


def inv_totient(t):
  """Returns the list of integers whose totient is t, in increasing order."""

  ps = [d + 1 for d in divisors(t) if is_prime(d + 1)]

  def generate(i, n, tr):
    # assert tr >= 1  # True, but skipped for performance.
    if tr == 1:
      yield n
    else:
      while i < len(ps):
        p = ps[i]
        if p - 1 > tr:  # Shortcut, no more primes can divide.
          break
        i += 1
        if tr % (p - 1) == 0:
          tr2 = tr / (p - 1)
          n2 = n * p
          for v in generate(i, n2, tr2):
            yield v
          while tr2 % p == 0:
            tr2 /= p
            n2 *= p
            for v in generate(i, n2, tr2):
              yield v

  return sorted(list(generate(0, 1, t)))


def yield_fib(a=0, b=1):
  """Yields the Fibonacci numbers indefinitely, starting with a and then b.

  Also works for non-Fibonacci starting numbers.

  Use fib_pair(...) to start from a large number.
  """
  while 1:
    yield a
    a, b = b, a + b


def fib_pair(n):
  """Returns the nth and (n+1)th Fibonacci number, fib_pair(0) == (0, 1).

  Uses fast doubling, does O(log n) basic arithmetic operations. (Each
  operation can be O(n) because of the large numbers involved.)
  """
  if n < 0:
    raise ValueError

  def fib_rec(n):
    """Returns a tuple (F(n), F(n + 1))."""
    if n == 0:
      return 0, 1
    else:
      a, b = fib_rec(n >> 1)
      c = a * ((b << 1) - a)
      d = b * b + a * a
      if n & 1:
        return d, c + d
      else:
        return c, d

  return fib_rec(n)


def fib(n):
  """Returns the nth Fibonacci number, fib(0) == 0.

  Uses fast doubling, does O(log n) basic arithmetic operations. (Each
  operation can be O(n) because of the large numbers involved.)

  If you need consecutive Fibonacci numbers, yield_fib is faster.
  """
  return fib_pair(n)[0]


def yield_fib_mod(m, a=0, b=1):
  """Yields the Fibonacci numbers mod m indefinitely mod m, starting with a, b.

  Also works for non-Fibonacci starting numbers.

  Use fib_pair(...) to start from a large number.
  """
  if not isinstance(m, (int, long)):
    raise TypeError
  if m <= 0:
    raise ValueError
  a %= m
  b %= m
  while 1:
    yield a
    a, b = b, (a + b) % m


def fib_pair_mod(n, m):
  """Returns the nth and (n+1)th Fibonacci number mod m,
  fib_pair(0, m) == (0, 1).

  Uses fast doubling, does O(log n) basic arithmetic operations. (Each
  operation can be O(n) because of the large numbers involved.)
  """
  if n < 0:
    raise ValueError

  def fib_rec(n):
    """Returns a tuple (F(n) % m, F(n + 1) % m)."""
    if n == 0:
      return 0, 1
    else:
      a, b = fib_rec(n >> 1)
      c = a * ((b << 1) - a) % m
      d = (b * b + a * a) % m
      if n & 1:
        return d, (c + d) % m
      else:
        return c, d

  return fib_rec(n)


def fib_mod(n, m):
  """Returns the nth Fibonacci number mod m, fib(0, m) == 0.

  Uses fast doubling, does O(log n) basic arithmetic operations. (Each
  operation can be O(n) because of the large numbers involved.)

  If you need consecutive Fibonacci numbers, yield_fib is faster.
  """
  return fib_pair_mod(n, m)[0]


def modinv(a, b):
  """Returns the modular inverse of a, modulo b. b must be positive.

  If gcd(a, b) != 1, then no modular inverse exists, and ValueError is raised.

  Invariant: a * modinv(a, b) % b == 0.
  """
  # Implementation inspired by http://rosettacode.org/wiki/Modular_inverse#C
  # TODO(pts): Is the alternative implementation in pyecm for odd b faster?
  a0, b0 = a, b
  if b <= 0:
    raise ValueError('Modulus must be positive, got args: ' + repr((a0, b0)))
  a %= b
  if a < 0:
    a += b
  x0, x1 = 0, 1
  if a == 0:
    if b == 1:
      return 0
    raise ValueError('No modular inverse of 0: ' + repr((a0, b0)))
  while a > 1:
    assert -b0 <= x0 < b0
    assert -b0 <= x1 < b0
    assert 1 < a <= b0
    assert 0 <= b <= b0
    if not b:
      raise ValueError('No modular inverse, not coprime: ' + repr((a0, b0)))
    x0, x1, a, b = x1 - a / b * x0, x0, b, a % b
  return x1 + (x1 < 0 and b0)


def crt2(a1, m1, a2, m2):
  """Compute and return x using the Chinese remainder theorem.

  m1 amd m2 are the moduluses, and they must be coprimes.

  Returns:
    An integer a which is: 0 <= a < m1 * m2 and a % m1 == a1 and a % m2 == a2.
  Raises:
    ValueError: Iff no such unique a exists, i.e. iff gcd(m1, m2) != 1.
  """
  a1 %= m1  # Also makes it positive.
  a2 %= m2  # Also makes it positive.
  # http://en.wikipedia.org/wiki/Chinese_remainder_theorem#Case_of_two_equations_.28k_.3D_2.29
  return (m2 * modinv(m2, m1) * a1 + m1 * modinv(m1, m2) * a2) % (m1 * m2)


def fast_exp_with_func(p, q, mul_func):
  """Returns p multiplid by itself q times, using mul_func.

  This is the interative version of
  http://en.wikipedia.org/wiki/Exponentiation_by_squaring

  For example, for integers:

  * p ** q == fast_exp_with_func(p, q, lambda a, b: a * b)
  * pow(p, q, mod) == fast_exp_with_func(p, q, lambda a, b: a * b % mod) if
    q >= 2. If q == 1, then fast_exp_with_func(p, q, ...) == p.

  Args:
    p: Value to be multiplied.
    q: Number of times to multiply. Must be a positive integer.
    mul_func: Multiplication function. mul_func must take 2 arguments, and it
      must be associative (unchecked).
  """
  if not isinstance(q, (int, long)):
    raise TypeError
  if not callable(mul_func):
    raise TypeError
  if q <= 0:
    raise ValueError(q)
  while not (q & 1):
    p = mul_func(p, p)
    q >>= 1
  r = p
  q -= 1
  while q:
    if q & 1:
      r = mul_func(r, p)
      q -= 1
    p = mul_func(p, p)
    q >>= 1
  return r


def yield_primitive_pythagorean_triples_upto(limit):
  """Yields the primitive Pythagorean triples in no particular order.

  The integer triple (a, b, c) is a Pythagorean triple iff 1 <= a and 1 <= b
  and 1 <= c and a ** 2 + b ** 2 == c ** 2. That Pythagorean triple is
  primitive iff gcd(a, b) == 1.

  All primitive Pythagorean triples are yielded in no particular order for
  which c <= limit. Exactly one of (a, b, c) and (b, a, c) are yielded.

  For each triple (a, b, c) yielded: 3 <= a and 4 <= b and 5 <= c <= limit and
  a % 2 == 1 and b % 2 == 0 and gcd(a, b) == 1 and a ** 2 + b ** 2 == c ** 2.

  Please note that one of (a < b) and (a > b) is true, the caller may want to
  try a and b in the opposite order.

  http://en.wikipedia.org/wiki/Pythagorean_triple#Generating_a_triple
  """
  sq = sqrt_floor(limit) + 1
  _gcd = gcd
  # The triple generated by Euclid's formula is primitive if and only if
  # i and j are coprime and i - j is odd (thus one of i is odd, and the other
  # one is even).
  for i in xrange(1, sq, 2):
    ii = i * i
    for j in xrange(2, sq, 2):
      if _gcd(i, j) == 1:
        jj = j * j
        kk = ii + jj
        if kk > limit:
          break
        # True but slow: assert gcd(abs(jj - ii), ((i * j) << 1)) == 1
        yield abs(jj - ii), ((i * j) << 1), kk


def yield_pythagorean_triples_upto(limit):
  """Yields the Pythagorean triples in no particular order.

  The integer triple (a, b, c) is a Pythagorean triple iff 1 <= a and 1 <= b
  and 1 <= c and a ** 2 + b ** 2 == c ** 2. That Pythagorean triple is
  primitive iff gcd(a, b) == 1.

  All (primitive and non-primitive) Pythagorean triples are yielded in no
  particular order for which c <= limit. Exactly one of (a, b, c) and (b, a,
  c) are yielded.

  For each triple (a, b, c) yielded: 3 <= a and 4 <= b and 5 <= c <= limit and
  a != b and a ** 2 + b ** 2 == c ** 2.

  Please note that one of (a < b) and (a > b) is true, the caller may want to
  try a and b in the opposite order.

  http://en.wikipedia.org/wiki/Pythagorean_triple#Generating_a_triple
  """
  limit1 = limit + 1
  sq = sqrt_floor(limit) + 1
  _gcd = gcd
  # The triple generated by Euclid's formula is primitive if and only if
  # i and j are coprime and i - j is odd (thus one of i is odd, and the other
  # one is even).
  for i in xrange(1, sq, 2):
    ii = i * i
    for j in xrange(2, sq, 2):
      if _gcd(i, j) == 1:
        jj = j * j
        kk = ii + jj
        if kk > limit:
          break
        qd = qq = abs(jj - ii)
        rd = rr = ((i * j) << 1)
        for ss in xrange(kk, limit1, kk):
          yield qq, rr, ss
          rr += rd
          qq += qd


def yield_pythagorean_triple_sums_upto(limit):
  """Yields the sums of Pythagorean triples in no particular order.

  The integer triple (a, b, c) is a Pythagorean triple iff 1 <= a and 1 <= b
  and 1 <= c and a ** 2 + b ** 2 == c ** 2. That Pythagorean triple is
  primitive iff gcd(a, b) == 1.

  The sum (a + b + c) of all (primitive and non-primitive) Pythagorean
  triples (a, b, c) are yielded in no particular order for which a + b + c
  <= limit. Exactly one of (a, b, c) and (b, a, c) are yielded.

  (a + b + c) is yielded for each triple (a, b, c) for which all these are
  true: 3 <= a and 4 <= b and 5 <= and a + b + c <= limit and a != b and a
  ** 2 + b ** 2 == c ** 2.

  Please note that the same sum may be yielded multiple times (e.g. 60 == 15
  + 20 + 25 == 10 + 24 + 26), but it will be yielded once in total for (a,
  b, c) and (b, a, c).

  http://en.wikipedia.org/wiki/Pythagorean_triple#Generating_a_triple
  """
  limit1 = limit + 1
  sq = sqrt_floor(limit) + 1
  _gcd = gcd
  # The triple generated by Euclid's formula is primitive if and only if
  # i and j are coprime and i - j is odd (thus one of i is odd, and the other
  # one is even).
  #
  # It's obvious that if i >= limit and j >= sqrt(limit), then uu >=
  # (sqrt(limit) + sqrt(limit) * sqrt(limit)) * 2 >= limit * 2 > limit, so
  # there is no solution (assuming limit >= 1). So having sq as the upper
  # limit in the xrange for both i and j won't lose any solutions. But we
  # can have a smaller upper limit for j by using the fact that limit >= uu ==
  # (i + j) ** 2 + abs(j * j - i * i) > (i * j) ** 2. (We used the fact that
  # i != j, because i is odd and j is even.) Thus sqrt(limit) > i + j, thus
  # sq > i + j, thus sq - i > j, thus sq - i is a good upper limit for j.
  for i in xrange(1, sq, 2):
    ii = i * i
    for j in xrange(2, sq - i, 2):
      if _gcd(i, j) == 1:
        uu = (max(ii, j * j) + i * j) << 1
        if uu > limit:
          break  # Safe to break since uu is increasing as j is increasing.
        # True but slow:
        # assert uu == abs(j * j - i * i) + ((i * j) << 1) + (j * j + i * i)
        # True but slow: assert uu == (i + j) ** 2 + abs(j * j - i * i)
        # True but slow: assert (i + j) ** 2 < limit
        # True but slow: assert i + j < sq  # But `i + j < sq - 1' can be false.
        for tt in xrange(uu, limit1, uu):
          yield tt


def yield_pythagorean_triples_perimeter_upto(limit):
  """Yields the Pythagorean triples in no particular order.

  The integer triple (a, b, c) is a Pythagorean triple iff 1 <= a and 1 <= b
  and 1 <= c and a ** 2 + b ** 2 == c ** 2. That Pythagorean triple is
  primitive iff gcd(a, b) == 1.

  All (primitive and non-primitive) Pythagorean triples are yielded in no
  particular order for which a + b + c <= limit. Exactly one of (a, b, c)
  and (b, a, c) are yielded.

  Similar to yield_pythagorean_triple_sums_upto, but this generator yields
  (a, b, c) and the other one yields (a + b + c).

  For each triple (a, b, c) yielded: 3 <= a and 4 <= b and 5 <= c <= limit and
  a != b and a ** 2 + b ** 2 == c ** 2.

  Please note that one of (a < b) and (a > b) is true, the caller may want to
  try a and b in the opposite order.

  http://en.wikipedia.org/wiki/Pythagorean_triple#Generating_a_triple
  """
  limit1 = limit + 1
  sq = sqrt_floor(limit) + 1
  _gcd = gcd
  # The triple generated by Euclid's formula is primitive if and only if
  # i and j are coprime and i - j is odd (thus one of i is odd, and the other
  # one is even).
  for i in xrange(1, sq, 2):
    ii = i * i
    # sq would obviously work as an upper limit for the xrange here. See the
    # comment in yield_pythagorean_triple_sums_upto explaining why `sq - i'
    # also works.
    for j in xrange(2, sq - i, 2):
      if _gcd(i, j) == 1:
        jj, ij = j * j, i * j
        uu = (max(ii, jj) + ij) << 1
        if uu > limit:
          break
        qd = qq = abs(jj - ii)
        rd = rr = (ij << 1)
        for tt in xrange(uu, limit1, uu):
          yield qq, rr, tt - qq - rr
          rr += rd
          qq += qd


def get_pell_base(dd):
  """Returns the smallest positive integer pair (x, y) for which x ** 2 - dd
  * y ** 2 = 1, or (0, 0) if dd is a perfect square (thus no solutions).

  Similar to get_pell_base_ary, but uses less memory (no array).

  Based on http://mathworld.wolfram.com/PellEquation.html :

  If dd is not a perfect square, then the solution (x, y) is (p[r], q[r]) if
  r is odd, or (p[2*r+1], q[2*r+1]) if r is even. r is the smallest positive
  index for which a[r+1] == 2 * a[0]. Here a[n] is the continued fraction
  expansion of sqrt(dd), and p[n]/q[n] is the convergent. Here is how to
  generate the series:

  a[0] := intalg.sqrt_floor(dd)
  pp[0] := 0; pp[1] := a[0]; pp[n] := a[n-1] * qq[n-1] - pp[n- 1].
  qq[0] := 1; qq[1] := dd - a[0]**2; qq[n] := (dd - pp[n]**2) / qq[n-1].
  a[n] := floor((a[0] + pp[n]) / qq[n])
  p[0] := a0; p[1] := a[0] * a[1] + 1; p[n] := a[n] * p[n-1] + p[n-2].
  q[0] := 1; q[1] := a[1]; q[n] := a[n] * q[n-1] + q[n-2].
  """
  a0 = sqrt_floor(dd)
  if a0 ** 2 == dd:
    return (0, 0)
  a0d = a0 << 1
  a1 = a0d // (dd - a0 ** 2)  # Floor, not divisble.
  an1, ppn1, qqn1 = a1, a0, dd - a0 ** 2
  pn2, pn1, qn2, qn1 = a0, a0 * a1 + 1, 1, a1
  n = -2
  while n:
    n -= 1
    ppn1 = an1 * qqn1 - ppn1
    qqn1 = (dd - ppn1 ** 2) // qqn1  # Always divisible and positive.
    an1 = (a0 + ppn1) // qqn1  # Floor, not divisible.
    if n < 0 and an1 == a0d:
      if n & 1:
        break
      n = -2 - n
    pn2, pn1, qn2, qn1 = pn1, an1 * pn1 + pn2, qn1, an1 * qn1 + qn2
  return (pn1, qn1)


def yield_rle_factorize_factorial(n):
  """Yields the RLEd prime factorization of factorial(n)."""
  if n < 0:
    raise ValueError
  for p in primes_upto(n):
    a = 0
    np = n / p
    while np:
      a += np
      np /= p
    yield (p, a)
