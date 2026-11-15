The automated gates rejected your delivery:

GATE mutation: FAILED. Mutation score 71.4% (25/35 killed), required >= 80%. Each surviving mutant is a change your tests did not detect:
  line 8: <= -> <   | if "a" <= char <= "z":
  line 9: return value -> return None   | return _LOWER
  line 10: <= -> <   | if "A" <= char <= "Z":
  line 11: return value -> return None   | return _UPPER
  line 12: <= -> <   | if "0" <= char <= "9":
  line 12: <= -> <   | if "0" <= char <= "9":
  line 13: return value -> return None   | return _DIGIT
  line 14: return value -> return None   | return _OTHER
  line 33: return value -> return None   | return False
  line 45: or -> and   | if not isinstance(password, str) or not isinstance(username, str):

Fix the problems. You may change `solution.py` and the tests. Run `python -m pytest -q tests` again, and stop when you are done.
