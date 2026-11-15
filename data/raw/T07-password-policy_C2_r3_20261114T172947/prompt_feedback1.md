The automated gates rejected your delivery:

GATE CRAP: FAILED. Every function must have CRAP < 10.0. CRAP = CC^2 * (1-coverage)^3 + CC, so reduce complexity and/or test more.
  check_password (line 28): complexity 10, coverage 100%, CRAP 10.0

GATE mutation: FAILED. Mutation score 69.0% (29/42 killed), required >= 80%. Each surviving mutant is a change your tests did not detect:
  line 3: 0 -> 1   | run = 0
  line 13: return value -> return None   | return False
  line 18: <= -> <   | has_lower = any("a" <= ch <= "z" for ch in password)
  line 18: <= -> <   | has_lower = any("a" <= ch <= "z" for ch in password)
  line 19: <= -> <   | has_upper = any("A" <= ch <= "Z" for ch in password)
  line 19: <= -> <   | has_upper = any("A" <= ch <= "Z" for ch in password)
  line 20: <= -> <   | has_digit = any("0" <= ch <= "9" for ch in password)
  line 20: <= -> <   | has_digit = any("0" <= ch <= "9" for ch in password)
  line 22: <= -> <   | not (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9"))
  line 22: <= -> <   | not (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9"))
  line 22: <= -> <   | not (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9"))
  line 22: <= -> <   | not (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9"))
  line 30: or -> and   | if not isinstance(password, str) or not isinstance(username, str):

Fix the problems. You may change `solution.py` and the tests. Run `python -m pytest -q tests` again, and stop when you are done.
