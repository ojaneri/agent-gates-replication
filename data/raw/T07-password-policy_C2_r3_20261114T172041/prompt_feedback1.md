The automated gates rejected your delivery:

GATE CRAP: FAILED. Every function must have CRAP < 10.0. CRAP = CC^2 * (1-coverage)^3 + CC, so reduce complexity and/or test more.
  check_password (line 23): complexity 10, coverage 100%, CRAP 10.0

GATE mutation: FAILED. Mutation score 74.4% (32/43 killed), required >= 80%. Each surviving mutant is a change your tests did not detect:
  line 2: <= -> <   | if "a" <= ch <= "z":
  line 3: return value -> return None   | return 0
  line 4: <= -> <   | if "A" <= ch <= "Z":
  line 5: return value -> return None   | return 1
  line 6: <= -> <   | if "0" <= ch <= "9":
  line 6: <= -> <   | if "0" <= ch <= "9":
  line 7: return value -> return None   | return 2
  line 8: return value -> return None   | return 3
  line 8: 3 -> 4   | return 3
  line 15: return value -> return None   | return False
  line 25: or -> and   | if not isinstance(password, str) or not isinstance(username, str):

Fix the problems. You may change `solution.py` and the tests. Run `python -m pytest -q tests` again, and stop when you are done.
