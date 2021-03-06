#! /usr/bin/python2.6

"""Fast unit tests for the intalg module."""

__author__ = 'pts@fazekas.hu (Peter Szabo)'

import array
import math
import unittest

import intalg


class IntalgSmokeTest(unittest.TestCase):
  def setUp(self):
    intalg.clear_prime_cache()

  def tearDown(self):
    intalg.clear_prime_cache()

  def testBitCount(self):
    self.assertEquals(1, intalg.bit_count(0))
    self.assertEquals(1, intalg.bit_count(1))
    self.assertEquals(2, intalg.bit_count(2))
    self.assertEquals(2, intalg.bit_count(3))
    self.assertEquals(6, intalg.bit_count(63))
    self.assertEquals(7, intalg.bit_count(64))
    self.assertEquals(7, intalg.bit_count(75))
    self.assertEquals(11, intalg.bit_count(2047))
    self.assertEquals(12, intalg.bit_count(2048))
    self.assertEquals(12, intalg.bit_count(-4007))
    self.assertEquals(12, intalg.bit_count(4095))
    self.assertEquals(13, intalg.bit_count(4096))
    self.assertEquals(1204, intalg.bit_count(1 << 1203))
    self.assertEquals(1204, intalg.bit_count(-(1 << 1203)))
    self.assertEquals(1205, intalg.bit_count(1 << 1204))
    self.assertEquals(1206, intalg.bit_count(1 << 1205))
    self.assertEquals(1207, intalg.bit_count(1 << 1206))

  def testLog256MoreTable(self):
    self.assertEquals(257, len(intalg.LOG2_256_MORE_TABLE))
    self.assertEquals(1762, intalg.LOG2_256_MORE_TABLE[0x76])
    self.assertEquals(1531, intalg.LOG2_256_MORE_TABLE[63])
    self.assertEquals(1536, intalg.LOG2_256_MORE_TABLE[64])
    self.assertEquals(1542, intalg.LOG2_256_MORE_TABLE[65])

  def testLog256More(self):
    self.assertEquals(1762, intalg.log2_256_more(0x76))  # Accurate.
    self.assertEquals(6882, intalg.log2_256_more(123456789))  # Accurate (by luck).
    self.assertEquals(2048, intalg.log2_256_more(256))
    self.assertEquals(2051, intalg.log2_256_more(257))  # 2050 is more accurate.
    self.assertEquals(2051, intalg.log2_256_more(258))
    self.assertEquals(2054, intalg.log2_256_more(259))
    self.assertEquals(123 << 8, intalg.log2_256_more(1 << 123))
    self.assertEquals(1203 << 8, intalg.log2_256_more(1 << 1203))
    self.assertEquals(1204 << 8, intalg.log2_256_more(1 << 1204))
    self.assertEquals(1205 << 8, intalg.log2_256_more(1 << 1205))
    self.assertEquals(1206 << 8, intalg.log2_256_more(1 << 1206))

  def testLog256LessTable(self):
    self.assertEquals(256, len(intalg.LOG2_256_LESS_TABLE))
    self.assertEquals(1761, intalg.LOG2_256_LESS_TABLE[0x76])
    self.assertEquals(1530, intalg.LOG2_256_LESS_TABLE[63])
    self.assertEquals(1536, intalg.LOG2_256_LESS_TABLE[64])
    self.assertEquals(1541, intalg.LOG2_256_LESS_TABLE[65])

  def testLog256Less(self):
    self.assertEquals(1761, intalg.log2_256_less(0x76))  # Accurate.
    self.assertEquals(6880, intalg.log2_256_less(123456789))  # 6681 is more accurate.
    self.assertEquals(2048, intalg.log2_256_less(256))
    self.assertEquals(2048, intalg.log2_256_less(257))  # Same as for 256, last bit ignored.
    self.assertEquals(2050, intalg.log2_256_less(258))
    self.assertEquals(2050, intalg.log2_256_less(259))  # Same as for 256, last bit ignored.
    self.assertEquals(123 << 8, intalg.log2_256_less(1 << 123))
    self.assertEquals(1203 << 8, intalg.log2_256_less(1 << 1203))
    self.assertEquals(1204 << 8, intalg.log2_256_less(1 << 1204))
    self.assertEquals(1205 << 8, intalg.log2_256_less(1 << 1205))
    self.assertEquals(1206 << 8, intalg.log2_256_less(1 << 1206))

  def testLogMore(self):
    b_coeff = 123457 * math.log(3)
    for i in xrange(100):
      a = intalg.log_more(123457, 3 ** i)
      b = b_coeff * i
      assert b <= a, (i, a, b)
      assert b + b / 256 >= a, (i, a, b)

  def testSqrtFloor(self):
    assert intalg.sqrt_floor(41 ** 6) == 41 ** 3
    assert intalg.sqrt_floor((41 ** 3 + 1) ** 2 - 1) == 41 ** 3
    assert intalg.sqrt_floor(10 ** 5000) == 10 ** 2500  # 10e5000 is float overflow.

    for n in xrange(100):
      r = intalg.sqrt_floor(n)
      rk = r * r
      assert rk <= n < (r + 1) ** 2, (n, r)

    for ni in xrange(100):
      n = int(37 + 100 * 1.5 ** ni)
      r = intalg.sqrt_floor(n)
      rk = r * r
      assert rk <= n < (r + 1) ** 2, (n, r)

  def testRootFloor(self):
    self.assertEquals((41 ** 3, True), intalg.root_floor(41 ** 6, 2))
    self.assertEquals((41 ** 2, True), intalg.root_floor(41 ** 6, 3))
    self.assertEquals((41, False), intalg.root_floor(42 ** 6 - 30 ** 6, 6))
    self.assertEquals((42 ** 2 - 1, False), intalg.root_floor(42 ** 6 - 13 ** 6, 3))
    self.assertEquals((10 ** 2500, True), intalg.root_floor(10 ** 5000, 2))  # 10e5000 > max_float.
    self.assertEquals((2, True), intalg.root_floor(2 ** 1000, 1000))
    self.assertEquals((3, True), intalg.root_floor(3 ** 1000, 1000))
    self.assertEquals((42 ** 3, True), intalg.root_floor(42 ** 9000, 3000))

    for k in (2, 3, 4, 5, 6, 7):
      for n in xrange(100):
        r, is_exact = intalg.root_floor(n, k)
        rk = r ** k
        assert rk <= n < (r + 1) ** k
        assert (rk == n) == is_exact, (n, k, r, is_exact, rk)

    for k in (2, 3, 4, 5, 6, 7):
      for ni in xrange(20):
        n = int(37 + 100000 * 3 ** ni)
        r, is_exact = intalg.root_floor(n, k)
        rk = r ** k
        assert rk <= n < (r + 1) ** k
        assert (rk == n) == is_exact, (n, k, r, is_exact, rk)

  def testFractionToFloat(self):
    self.assertEquals(32.5, intalg.fraction_to_float(2 ** 10005 + 2 ** 9999, 2 ** 10000))
    self.assertEquals(32.5, intalg.fraction_to_float(2 ** 10005 + 2 ** 9999 + 1, 2 ** 10000))

  def testPrimesUpto(self):
    self.assertEquals([2, 3, 5, 7, 11, 13, 17, 19], intalg.primes_upto(22))
    self.assertEquals([2, 3, 5, 7, 11, 13, 17, 19, 23], intalg.primes_upto(23))
    self.assertEquals([2, 3, 5, 7, 11, 13, 17, 19, 23], intalg.primes_upto(24))
    primes = intalg.primes_upto(100)
    self.assertEquals([1], intalg._prime_cache_limit_ary[:])
    self.assertEquals(None, intalg.prime_index(100))
    self.assertEquals(len(primes) - 1, intalg.prime_index(97))
    self.assertEquals(primes, intalg.primes_upto(100))
    self.assertEquals(primes, intalg.primes_upto(97))

    intalg._prime_cache[:] = [6, 77, 8]
    primes3 = intalg.primes_upto(100)
    self.assertEquals([6, 77, 8], primes3)  # Because of the fake _prime_cache.

  def testFirstPrimesMoremem(self):
    self.assertEquals([], intalg.first_primes_moremem(0))
    self.assertEquals([2], intalg.first_primes_moremem(1))
    self.assertEquals([2, 3, 5, 7, 11, 13, 17, 19],
                      intalg.first_primes_moremem(8))
    self.assertEquals([2, 3, 5, 7, 11, 13, 17, 19, 23],
                      intalg.first_primes_moremem(9))
    primes = intalg.first_primes_moremem(100)
    self.assertEquals(100, len(primes))
    self.assertEquals([1], intalg._prime_cache_limit_ary[:])
    self.assertEquals(len(primes) - 1, intalg.prime_index(primes[-1]))
    self.assertEquals([1024], intalg._prime_cache_limit_ary[:])
    primes2 = intalg.first_primes_moremem(100)
    self.assertEquals(primes, primes2)

    intalg._prime_cache[0] = 6
    primes3 = intalg.first_primes_moremem(100)
    primes3_exp = primes2[:]
    primes3_exp[0] = 6
    self.assertEquals(primes3_exp, primes3)  # Because of the fake _prime_cache.

  def testFirstPrimes(self):
    self.assertEquals([], intalg.first_primes(0))
    self.assertEquals([2], intalg.first_primes(1))
    self.assertEquals([2, 3, 5, 7, 11, 13, 17, 19],
                      intalg.first_primes(8))
    self.assertEquals([2, 3, 5, 7, 11, 13, 17, 19, 23],
                      intalg.first_primes(9))
    primes = intalg.first_primes(100)
    self.assertEquals(100, len(primes))
    self.assertEquals([1], intalg._prime_cache_limit_ary[:])
    self.assertEquals(len(primes) - 1, intalg.prime_index(primes[-1]))
    self.assertEquals([1024], intalg._prime_cache_limit_ary[:])
    primes2 = intalg.first_primes(100)
    self.assertEquals(primes, primes2)

    intalg._prime_cache[0] = 6
    primes3 = intalg.first_primes(100)
    primes3_exp = primes2[:]
    primes3_exp[0] = 6
    self.assertEquals(primes3_exp, primes3)  # Because of the fake _prime_cache.

  def testYieldSlowFactorize(self):
    self.assertEquals(list(intalg.yield_slow_factorize(1)), [])
    self.assertEquals(list(intalg.yield_slow_factorize(36)), [2, 2, 3, 3])
    self.assertEquals(list(intalg.yield_slow_factorize(180)), [2, 2, 3, 3, 5])
    self.assertEquals(list(intalg.yield_slow_factorize(3 ** 1000 * 29 ** 57)), [3] * 1000 + [29] * 57)
    self.assertEquals(list(intalg.yield_slow_factorize(2 * 3 * 5 * 7 * 7 * 11 * 13 * 17 * 19)), [2, 3, 5, 7, 7, 11, 13, 17, 19])

  def testFactorizeMedium(self):
    n = intalg.next_prime(intalg._SMALL_PRIME_LIMIT) ** 2 - 10
    limit = n + 100
    while n < limit:  # xrange can't take a long (n).
      a = list(intalg.yield_slow_factorize(n))
      b = intalg.finder_slow_factorize(n)
      c = intalg.factorize(n)
      d = intalg.factorize(n, divisor_finder=intalg.brent)
      e = intalg.factorize(n, divisor_finder=intalg.pollard)
      assert a == b == c == d == e, (n, a, b, c, d, e)
      n += 1

  def testFactorizeSmall(self):
    for n in xrange(1, 100):
      a = list(intalg.yield_slow_factorize(n))
      b = intalg.finder_slow_factorize(n)
      c = intalg.factorize(n, divisor_finder=intalg.brent)
      d = intalg.factorize(n, divisor_finder=intalg.pollard)
      assert a == b == c == d, (n, a, b, c, d)

  def testBrentPrime(self):
    random_obj = intalg.MiniIntRandom(42)
    for n in intalg.primes_upto(100):
      b = intalg.brent(n, random_obj)
      self.assertEquals(b, n)

  def testPollardPrime(self):
    random_obj = intalg.MiniIntRandom(42)
    for n in intalg.primes_upto(100):
      b = intalg.pollard(n, random_obj)
      self.assertEquals(b, n)

  def testBrentComposite(self):
    random_obj = intalg.MiniIntRandom(42)
    for n in intalg.yield_composites():
      if n > 100:
        break
      b = intalg.brent(n, random_obj)
      assert b > 1
      assert b <= n
      self.assertEquals(0, n % b, (b, n))

  def testPollardComposite(self):
    random_obj = intalg.MiniIntRandom(42)
    for n in intalg.yield_composites():
      if n > 100:
        break
      b = intalg.pollard(n, random_obj)
      assert b > 1
      assert b <= n
      self.assertEquals(0, n % b, (b, n))

  def testTotient(self):
    expected = [0, 1, 1, 2, 2, 4, 2, 6, 4, 6, 4, 10, 4, 12, 6, 8, 8, 16, 6,
                18, 8, 12, 10, 22]
    self.assertEquals([0], intalg.totients_upto(0))
    self.assertEquals([0], intalg.totients_upto(0, force_recursive=1))
    self.assertEquals([0, 1], intalg.totients_upto(1, force_recursive=1))
    self.assertEquals([0, 1], intalg._totients_upto_iterative(1))
    self.assertEquals([0, 1, 1], intalg.totients_upto(2, force_recursive=1))
    self.assertEquals([0, 1, 1], intalg._totients_upto_iterative(2))
    self.assertEquals(expected, intalg.totients_upto(23))
    self.assertEquals(expected, intalg.totients_upto(23, force_recursive=1))
    self.assertEquals(expected, intalg._totients_upto_iterative(23))
    self.assertEquals(expected, map(intalg.totient, xrange(24)))
    result = [None] * 24
    result[0] = 0
    for n, t in intalg.yield_totients_upto(23):
      result[n] = t
    self.assertEquals(expected, result)
    limit = 500
    expected2 = map(intalg.totient, xrange(limit + 1))
    self.assertEquals(expected2, intalg.totients_upto(limit))
    self.assertEquals(expected2, intalg.totients_upto(limit, force_recursive=1))
    self.assertEquals(expected2, intalg._totients_upto_iterative(limit))

  def testDivisorCountsUpto(self):
    expected = [0, 1, 2, 2, 3, 2, 4, 2, 4, 3, 4, 2, 6, 2, 4, 4, 5, 2, 6, 2, 6, 4, 4,
         2, 8, 3, 4, 4, 6, 2, 8, 2, 6, 4, 4, 4, 9, 2, 4, 4, 8, 2, 8, 2, 6, 6,
         4, 2, 10, 3, 6, 4, 6, 2, 8, 4, 8, 4, 4, 2, 12, 2, 4, 6, 7, 4, 8, 2,
         6, 4, 8, 2, 12, 2, 4, 6, 6, 4, 8, 2, 10, 5, 4, 2, 12, 4, 4, 4, 8, 2,
         12, 4, 6, 4, 4, 4, 12, 2, 6, 6, 9]
    self.assertEquals(expected, intalg.divisor_counts_upto(100))
    a = [()] * 101
    self.assertTrue(a is intalg.divisor_counts_upto(100, a))
    self.assertEquals(expected, a)
    a = array.array('I', (0,)) * 101
    self.assertTrue(a is intalg.divisor_counts_upto(100, a))
    self.assertEquals(array.array('I', expected), a)

  def testDivisors(self):
    self.assertEquals([1], intalg.divisors(1))
    self.assertEquals([1, 2, 3, 4, 6, 12], intalg.divisors(12))

  def testInvTotient(self):
    self.assertEquals([1], intalg.inv_totient(1))
    self.assertEquals([3, 4, 6], intalg.inv_totient(2))
    self.assertEquals([], intalg.inv_totient(3))
    self.assertEquals([5, 8, 10, 12], intalg.inv_totient(4))
    self.assertEquals(
        [73, 91, 95, 111, 117, 135, 146, 148, 152, 182, 190,
         216, 222, 228, 234, 252, 270], intalg.inv_totient(72))

  def testPrimeIndex(self):
    self.assertEquals(2, intalg.prime_index(5))
    self.assertEquals([256], intalg._prime_cache_limit_ary[:])
    self.assertEquals(2, intalg.prime_index(5))
    self.assertEquals(None, intalg.prime_index(4))
    self.assertEquals(1, intalg.prime_index(3))
    self.assertEquals(0, intalg.prime_index(2))
    self.assertEquals(None, intalg.prime_index(1))
    self.assertEquals(None, intalg.prime_index(0))
    self.assertEquals(None, intalg.prime_index(255))
    self.assertEquals(len(intalg._prime_cache) - 1, intalg.prime_index(251))
    self.assertEquals(len(intalg._prime_cache) - 1, intalg.prime_index(251))
    self.assertEquals([256], intalg._prime_cache_limit_ary[:])
    # Grows the cache.
    self.assertEquals(intalg.prime_index(251) + 1, intalg.prime_index(257))
    self.assertEquals([512], intalg._prime_cache_limit_ary[:])
    self.assertEquals(intalg.prime_index(251) + 1, intalg.prime_index(257, 600))
    self.assertEquals([512], intalg._prime_cache_limit_ary[:])
    self.assertEquals(None, intalg.prime_index(600, 600))
    self.assertEquals([600], intalg._prime_cache_limit_ary[:])
    self.assertEquals(109, intalg.prime_index(601, limit=155))
    self.assertEquals([620], intalg._prime_cache_limit_ary[:])

  def testPrimeCountCached(self):
    self.assertEquals(3, intalg.prime_count_cached(6))
    self.assertEquals(3, intalg.prime_count_cached(5))
    self.assertEquals([256], intalg._prime_cache_limit_ary[:])
    self.assertEquals(3, intalg.prime_count_cached(5))
    self.assertEquals(2, intalg.prime_count_cached(4))
    self.assertEquals(2, intalg.prime_count_cached(3))
    self.assertEquals(1, intalg.prime_count_cached(2))
    self.assertEquals(0, intalg.prime_count_cached(1))
    self.assertEquals(0, intalg.prime_count_cached(0))
    self.assertEquals(54, intalg.prime_count_cached(255))
    self.assertEquals(len(intalg._prime_cache), intalg.prime_count_cached(251))
    self.assertEquals(len(intalg._prime_cache), intalg.prime_count_cached(251))
    self.assertEquals([256], intalg._prime_cache_limit_ary[:])
    # Grows the cache.
    self.assertEquals(intalg.prime_count_cached(251) + 1,
                      intalg.prime_count_cached(257))
    self.assertEquals([512], intalg._prime_cache_limit_ary[:])
    self.assertEquals(intalg.prime_count_cached(251) + 1,
                      intalg.prime_count_cached(257, 600))
    self.assertEquals([512], intalg._prime_cache_limit_ary[:])
    self.assertEquals(109, intalg.prime_count_cached(600, 600))
    self.assertEquals([600], intalg._prime_cache_limit_ary[:])
    self.assertEquals(110, intalg.prime_count_cached(601, limit=155))
    self.assertEquals([620], intalg._prime_cache_limit_ary[:])
    self.assertEquals(110, intalg.prime_count_cached(602))

  def testPrimeCount(self):
    intalg.clear_prime_cache()
    prime_counts1 = map(intalg.prime_count_cached, xrange(3000))
    intalg.clear_prime_cache()
    prime_counts2 = map(intalg.prime_count_cached, xrange(3000))
    prime_counts2 = map(intalg.prime_count_cached, xrange(3000))
    # TODO(pts): Add tests for prime_count_lowmem.
    self.assertEquals(prime_counts1, prime_counts2)

  def testPrimeCountMore(self):
    prime_counts = map(intalg.prime_count_cached, xrange(3000))
    prime_counts2 = map(intalg.prime_count_more, xrange(3000))
    self.assertEquals([True], list(set((
        a <= b for a, b in zip(prime_counts, prime_counts2)))))
    self.assertFalse(prime_counts == prime_counts2)  # Not accurate.
    self.assertEquals(prime_counts[:127], prime_counts2[:127])
    # Default accuracy.
    prime_counts3 = [intalg.prime_count_more(n, 100000) for n in xrange(3000)]
    self.assertEquals([True], list(set((
        a <= b for a, b in zip(prime_counts, prime_counts3)))))
    self.assertEquals(prime_counts2, prime_counts3)
    self.assertEquals([True], list(set((
        a * 11 > b * 10  # Accurate enough.
        for a, b in zip(prime_counts, prime_counts3)[2:]))))

    # Better accuracy.
    prime_counts4 = [intalg.prime_count_more(n, 50000) for n in xrange(3000)]
    self.assertEquals([True], list(set((
        a <= b for a, b in zip(prime_counts, prime_counts4)))))
    self.assertFalse(prime_counts == prime_counts4)  # Not accurate.
    self.assertEquals(prime_counts[:547], prime_counts4[:547])
    self.assertEquals([True], list(set((
        a * 105 > b * 100  # Accurate enough.
        for a, b in zip(prime_counts, prime_counts4)[2:]))))

  def testIsPrime(self):
    limit = 100
    primes = intalg.primes_upto(limit)
    self.assertEquals(97, primes[-1])
    primes2 = [n for n in xrange(limit + 1) if intalg.is_prime(n)]
    self.assertEquals(primes, primes2)
    self.assertEquals('True', repr(intalg.is_prime(97)))
    self.assertEquals('False', repr(intalg.is_prime(98)))
    self.assertEquals('False', repr(intalg.is_prime(99)))
    self.assertEquals('False', repr(intalg.is_prime(100)))

    self.assertEquals([1], intalg._prime_cache_limit_ary[:])
    intalg.prime_index(257)
    self.assertEquals([512], intalg._prime_cache_limit_ary[:])
    primes3 = [n for n in xrange(99) if intalg.is_prime(n)]
    self.assertEquals(primes, primes3)

    limit = 1009
    primes = intalg.primes_upto(limit)
    self.assertEquals(1009, primes[-1])
    primes2 = [n for n in xrange(limit + 1) if intalg.is_prime(n)]
    self.assertEquals(primes, primes2)

    del intalg._prime_cache[:]
    primes4 = [n for n in xrange(99) if intalg.is_prime(n)]
    self.assertEquals([2], primes4)  # Because of the fake empty _prime_cache.

  def testFib(self):
    """Unit tests for fib, yield_fib and fib_pari."""
    limit = 300
    f = intalg.yield_fib()
    a = []
    while len(a) < limit:
      a.append(f.next())
    self.assertEquals(
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987,
         1597, 2584, 4181], a[:20])
    self.assertEquals(a, map(intalg.fib, xrange(limit)))
    self.assertEquals(a, [intalg.fib_pair(x)[0] for x in xrange(limit)])
    self.assertEquals(a[1:], [intalg.fib_pair(x)[1] for x in xrange(limit - 1)])
    f = intalg.yield_fib(0, 10)
    a10 = []
    while len(a10) < limit:
      a10.append(f.next())
    self.assertEquals([10 * x for x in a], a10)
    f = intalg.yield_fib(*intalg.fib_pair(30))
    self.assertEquals(a[30], f.next())
    self.assertEquals(a[31], f.next())
    self.assertEquals(a[32], f.next())

  def testFibMod(self):
    """Unit tests for fib, yield_fib and fib_pari."""
    limit, m = 300, 1000
    f = intalg.yield_fib_mod(m)
    a = []
    while len(a) < limit:
      a.append(f.next())
    self.assertEquals(
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987,
         597, 584, 181], a[:20])
    self.assertEquals(a, [intalg.fib_mod(x, m) for x in xrange(limit)])
    self.assertEquals(a, [intalg.fib_pair_mod(x, m)[0] for x in xrange(limit)])
    self.assertEquals(a[1:], [
        intalg.fib_pair_mod(x, m)[1] for x in xrange(limit - 1)])
    self.assertEquals(tuple(a[30 : 32]), intalg.fib_pair_mod(30, m))
    f = intalg.yield_fib_mod(m, *intalg.fib_pair_mod(30, m))
    self.assertEquals(a[30], f.next())
    self.assertEquals(a[31], f.next())
    self.assertEquals(a[32], f.next())
    f = intalg.yield_fib_mod(m, 11, 13)
    a11 = []
    while len(a11) < 20:
      a11.append(f.next())
    self.assertEquals(
        [11, 13, 24, 37, 61, 98, 159, 257, 416, 673, 89, 762, 851, 613, 464,
         77, 541, 618, 159, 777], a11)

  def testModinv(self):
    self.assertEquals(intalg.modinv(2 ** 8, 7 ** 8), 4301082)
    self.assertEquals(intalg.modinv(7 ** 8, 2 ** 8), 65)
    self.assertEquals(intalg.modinv(55, 144), 55)
    self.assertEquals(intalg.modinv(89, 144), 89)
    self.assertEquals(intalg.modinv(2, 7), 4)
    self.assertEquals(intalg.modinv(42, 2017), 1969)
    self.assertEquals(intalg.modinv(0, 1), 0)
    self.assertEquals(intalg.modinv(100, 1), 0)
    self.assertEquals(intalg.modinv(0, 1), 0)
    self.assertEquals(intalg.modinv(100, 1), 0)
    self.assertEquals(intalg.modinv(75, 1), 0)
    self.assertEquals(intalg.modinv(1, 7 ** 8), 1)
    self.assertEquals(intalg.modinv(1, 7), 1)
    self.assertEquals(intalg.modinv(1, 2017), 1)
    self.assertEquals(intalg.modinv(1, 1), 0)
    self.assertEquals(intalg.modinv(-1, 7 ** 8), 7 ** 8 - 1)
    self.assertEquals(intalg.modinv(-1, 7), 7 - 1)
    self.assertEquals(intalg.modinv(-1, 2017), 2017 - 1)
    self.assertEquals(intalg.modinv(-1, 1), 0)
    self.assertEquals(intalg.modinv(-1, 6), 5)
    self.assertRaises(ValueError, intalg.modinv, 2, 4)
    self.assertRaises(ValueError, intalg.modinv, 5, 75)
    self.assertRaises(ValueError, intalg.modinv, 0, 100)

  def testCrt2(self):
    self.assertEquals(intalg.crt2(3, 10, 6, 9), 33)
    self.assertEquals(intalg.crt2(3, 10, 3, 9), 3)
    self.assertEquals(intalg.crt2(3, 10, 0, 9), 63)
    self.assertRaises(ValueError, intalg.crt2, 5, 10, 7, 12)
    for a1 in xrange(-10, 22):
      for a2 in xrange(-10, 22):
        a = intalg.crt2(a1, 10, a2, 9)
        assert 0 <= a < 90
        assert a % 10 == a1 % 10
        assert a % 9 == a2 % 9

  def testYieldFactorizeUpto(self):
    self.assertEquals(sorted(list(intalg.yield_factorize_upto(100))),
                      [(i, intalg.factorize(i)) for i in xrange(1, 101)])

  def testFastExpWithFunc(self):
    f = intalg.fast_exp_with_func
    for p in xrange(2, 12):
      for q in xrange(1, 33):
        assert p ** q == f(p, q, lambda a, b: a * b)
    for p in xrange(2, 12):
      for q in xrange(1, 33):
        for mod in xrange(2, 15):
          if q == 1:
            assert p == f(p, q, lambda a, b: a * b % mod)
          else:
            assert pow(p, q, mod) == f(p, q, lambda a, b: a * b % mod)

  def testDivisorSum(self):
    expected = [
        1, 3, 4, 7, 6, 12, 8, 15, 13, 18, 12, 28, 14, 24, 24, 31, 18, 39, 20,
        42, 32, 36, 24, 60, 31, 42, 40, 56, 30, 72, 32, 63, 48, 54, 48, 91, 38,
        60, 56, 90, 42, 96, 44, 84, 78, 72, 48, 124, 57, 93, 72, 98, 54, 120,
        72, 120, 80, 90, 60, 168, 62, 96, 104, 127, 84, 144, 68, 126, 96, 144,
        72, 195, 74, 114, 124, 140, 96, 168, 80, 186, 121, 126, 84, 224, 108,
        132, 120, 180, 90, 234, 112, 168, 128, 144, 120, 252, 98, 171, 156, 217]
    self.assertEquals([intalg.divisor_sum(i) for i in xrange(1, 101)],
                      expected)
    self.assertEquals([intalg.divisor_sum(intalg.factorize(i))
                       for i in xrange(1, 101)],
                      expected)

  def testYieldPrimitivePythagoreanTriplesUpto(self):
    ypptu = intalg.yield_primitive_pythagorean_triples_upto
    self.assertEquals(sorted(ypptu(0)), [])
    self.assertEquals(sorted(ypptu(1)), [])
    self.assertEquals(sorted(ypptu(4)), [])
    self.assertEquals(sorted(ypptu(5)), [(3, 4, 5)])
    self.assertEquals(sorted(ypptu(12)), [(3, 4, 5)])
    self.assertEquals(sorted(ypptu(13)), [(3, 4, 5), (5, 12, 13)])
    self.assertEquals(sorted(ypptu(20)), [(3, 4, 5), (5, 12, 13), (15, 8, 17)])
    self.assertEquals(sorted(ypptu(26)),
                      [(3, 4, 5), (5, 12, 13), (7, 24, 25), (15, 8, 17)])

  def testYieldPythagoreanTriplesUpto(self):
    yptu = intalg.yield_pythagorean_triples_upto
    self.assertEquals(sorted(yptu(0)), [])
    self.assertEquals(sorted(yptu(1)), [])
    self.assertEquals(sorted(yptu(4)), [])
    self.assertEquals(sorted(yptu(5)), [(3, 4, 5)])
    self.assertEquals(sorted(yptu(12)), [(3, 4, 5), (6, 8, 10)])
    self.assertEquals(sorted(yptu(13)), [(3, 4, 5), (5, 12, 13), (6, 8, 10)])
    self.assertEquals(sorted(yptu(20)),
                      [(3, 4, 5), (5, 12, 13), (6, 8, 10), (9, 12, 15),
                       (12, 16, 20), (15, 8, 17)])
    self.assertEquals(sorted(yptu(26)),
                      [(3, 4, 5), (5, 12, 13), (6, 8, 10), (7, 24, 25),
                       (9, 12, 15), (10, 24, 26), (12, 16, 20), (15, 8, 17),
                       (15, 20, 25)])

  def testYieldPythagoreanTripleSumsUpto(self):
    yptsu = intalg.yield_pythagorean_triple_sums_upto
    self.assertEquals(sorted(yptsu(0)), [])
    self.assertEquals(sorted(yptsu(1)), [])
    self.assertEquals(sorted(yptsu(11)), [])
    self.assertEquals(sorted(yptsu(12)), [12])
    self.assertEquals(sorted(yptsu(100)),
                      [12, 24, 30, 36, 40, 48, 56, 60, 60, 70, 72, 80, 84, 84,
                       90, 90, 96])
    self.assertEquals(sorted(yptsu(61)),
                      [12, 24, 30, 36, 40, 48, 56, 60, 60])
    self.assertEquals(sorted(yptsu(60)),
                      [12, 24, 30, 36, 40, 48, 56, 60, 60])
    self.assertEquals(sorted(yptsu(59)),
                      [12, 24, 30, 36, 40, 48, 56])

  def testYieldPythagoreanTriplesPerimeterUpto(self):
    yptpu = intalg.yield_pythagorean_triples_perimeter_upto
    self.assertEquals(sorted(yptpu(0)), [])
    self.assertEquals(sorted(yptpu(1)), [])
    self.assertEquals(sorted(yptpu(11)), [])
    self.assertEquals(sorted(yptpu(12)), [(3, 4, 5)])
    self.assertEquals(sorted(yptpu(100)), [
        (3, 4, 5), (5, 12, 13), (6, 8, 10), (7, 24, 25), (9, 12, 15), (9,
        40, 41), (10, 24, 26), (12, 16, 20), (15, 8, 17), (15, 20, 25), (15,
        36, 39), (18, 24, 30), (21, 20, 29), (21, 28, 35), (24, 32, 40),
        (30, 16, 34), (35, 12, 37)])
    expected = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (7, 24, 25),
                (9, 12, 15), (10, 24, 26), (12, 16, 20), (15, 8, 17),
                (15, 20, 25)]
    self.assertEquals(sorted(yptpu(61)), expected)
    self.assertEquals(sorted(yptpu(60)), expected)
    self.assertEquals(sorted(yptpu(59)), [
        (3, 4, 5), (5, 12, 13), (6, 8, 10), (7, 24, 25), (9, 12, 15),
        (12, 16, 20), (15, 8, 17)])
    yptsu = intalg.yield_pythagorean_triple_sums_upto
    self.assertEquals(map(sum, yptpu(60)), list(yptsu(60)))

  def testGetPellBase(self):
    assert [intalg.get_pell_base(i) for i in xrange(111)] == [
        (0, 0), (0, 0), (3, 2), (2, 1), (0, 0), (9, 4), (5, 2), (8, 3), (3,
        1), (0, 0), (19, 6), (10, 3), (7, 2), (649, 180), (15, 4), (4, 1),
        (0, 0), (33, 8), (17, 4), (170, 39), (9, 2), (55, 12), (197, 42),
        (24, 5), (5, 1), (0, 0), (51, 10), (26, 5), (127, 24), (9801, 1820),
        (11, 2), (1520, 273), (17, 3), (23, 4), (35, 6), (6, 1), (0, 0),
        (73, 12), (37, 6), (25, 4), (19, 3), (2049, 320), (13, 2), (3482,
        531), (199, 30), (161, 24), (24335, 3588), (48, 7), (7, 1), (0, 0),
        (99, 14), (50, 7), (649, 90), (66249, 9100), (485, 66), (89, 12),
        (15, 2), (151, 20), (19603, 2574), (530, 69), (31, 4), (1766319049,
        226153980), (63, 8), (8, 1), (0, 0), (129, 16), (65, 8), (48842,
        5967), (33, 4), (7775, 936), (251, 30), (3480, 413), (17, 2),
        (2281249, 267000), (3699, 430), (26, 3), (57799, 6630), (351, 40),
        (53, 6), (80, 9), (9, 1), (0, 0), (163, 18), (82, 9), (55, 6),
        (285769, 30996), (10405, 1122), (28, 3), (197, 21), (500001, 53000),
        (19, 2), (1574, 165), (1151, 120), (12151, 1260), (2143295, 221064),
        (39, 4), (49, 5), (62809633, 6377352), (99, 10), (10, 1), (0, 0),
        (201, 20), (101, 10), (227528, 22419), (51, 5), (41, 4), (32080051,
        3115890), (962, 93), (1351, 130), (158070671986249, 15140424455100),
        (21, 2)]

  def testYieldRleFactorizeFactorial(self):
    f = intalg.yield_rle_factorize_factorial
    self.assertEquals((), tuple(f(0)))
    self.assertEquals((), tuple(f(1)))
    self.assertEquals(((2, 1),), tuple(f(2)))
    self.assertEquals(((2, 1), (3, 1)), tuple(f(3)))
    self.assertEquals(((2, 3), (3, 1)), tuple(f(4)))
    self.assertEquals(((2, 3), (3, 1), (5, 1)), tuple(f(5)))
    self.assertEquals(
        ((2, 117), (3, 59), (5, 28), (7, 19), (11, 12), (13, 9), (17, 7),
         (19, 6), (23, 5), (29, 4), (31, 3), (37, 3), (41, 3), (43, 2),
         (47, 2), (53, 2), (59, 2), (61, 2), (67, 1), (71, 1), (73, 1),
         (79, 1), (83, 1), (89, 1), (97, 1), (101, 1), (103, 1), (107, 1),
         (109, 1), (113, 1)), tuple(f(123)))


if __name__ == '__main__':
  unittest.main()
