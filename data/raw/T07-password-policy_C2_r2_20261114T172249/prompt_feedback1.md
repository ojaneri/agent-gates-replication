The automated gates rejected your delivery:

GATE CRAP: FAILED. Every function must have CRAP < 10.0. CRAP = CC^2 * (1-coverage)^3 + CC, so reduce complexity and/or test more.
  check_password (line 18): complexity 10, coverage 100%, CRAP 10.0

GATE mutation: FAILED. Mutation score 68.9% (31/45 killed), required >= 80%. Each surviving mutant is a change your tests did not detect:
  line 3: <= -> <   | has_lower = any("a" <= ch <= "z" for ch in password)
  line 3: <= -> <   | has_lower = any("a" <= ch <= "z" for ch in password)
  line 4: <= -> <   | has_upper = any("A" <= ch <= "Z" for ch in password)
  line 5: <= -> <   | has_digit = any("0" <= ch <= "9" for ch in password)
  line 5: <= -> <   | has_digit = any("0" <= ch <= "9" for ch in password)
  line 6: remove 'not'   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 6: or -> and   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 6: <= -> <   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 6: <= -> <   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 6: <= -> <   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 6: <= -> <   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 6: <= -> <   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 6: <= -> <   | has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
  line 15: return value -> return None   | return False

Fix the problems. You may change `solution.py` and the tests. Run `python -m pytest -q tests` again, and stop when you are done.
