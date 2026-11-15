The automated gates rejected your delivery:

GATE mutation: FAILED. Mutation score 75.6% (31/41 killed), required >= 80%. Each surviving mutant is a change your tests did not detect:
  line 2: <= -> <   | if "a" <= ch <= "z":
  line 3: return value -> return None   | return 0
  line 4: <= -> <   | if "A" <= ch <= "Z":
  line 5: return value -> return None   | return 1
  line 6: <= -> <   | if "0" <= ch <= "9":
  line 6: <= -> <   | if "0" <= ch <= "9":
  line 7: return value -> return None   | return 2
  line 8: return value -> return None   | return 3
  line 8: 3 -> 4   | return 3
  line 29: or -> and   | if not isinstance(password, str) or not isinstance(username, str):

Fix the problems. You may change `solution.py` and the tests. Run `python -m pytest -q tests` again, and stop when you are done.
