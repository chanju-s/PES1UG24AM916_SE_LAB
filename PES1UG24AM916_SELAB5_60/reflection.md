# Lab 5: Static Code Analysis - Reflection

## 1. Which issues were the easiest to fix, and which were the hardest?

The easiest were the mechanical ones: unused imports, snake_case names, blank lines, and replacing yaml.load with yaml.safe_load. Each had a one-line fix that the tool described exactly. The hardest were the logic bugs the tools never reported: the room overfilling because of > instead of >=, gender being ignored, vacating not freeing the bed, and the XSS in the Flask page. I had to run the program, notice the wrong output, and trace the cause myself. Removing the remote logging listener was also a design decision, not just an edit.

## 2. Did the tools report any false positives, or issues you chose not to fix?

Bandit B311 on random.sample is arguably a false positive, since a room lottery is not cryptography. I still switched to secrets.SystemRandom because it is cheap and makes the lottery harder to predict. The module-level global state (rooms, allocations, waitlist) was not flagged but is a design weakness; I left it because moving it into a class is beyond the scope of this lab. Every other finding was a real problem.

## 3. How would you integrate static analysis into your development workflow?

I would run Flake8 and Pylint in the editor for instant feedback and add a pre-commit hook so style errors never reach a commit. In CI, such as GitHub Actions, I would run Pylint with a minimum score (for example --fail-under=9.5) and Bandit failing on medium and high findings, so a pull request cannot merge with new problems. Suppressions such as # nosec or # pylint: disable would be rare and always explained in a comment.

## 4. What tangible improvements did you see in code quality, security and robustness?

Pylint went from 5.84 to 10.00, Flake8 from 20 findings to 0, and Bandit from 5 findings (1 High, 2 Medium, 2 Low) to none. Security improved: no debugger exposure, no arbitrary-object YAML loading, no open logging socket, no hardcoded password, and no XSS. Robustness improved: rooms respect capacity and gender, duplicate allocations are blocked, vacating frees the bed, vacant-bed counts and fees are correct, and seniors come first. Static analysis catches style problems and known-dangerous patterns well but cannot judge intent, so it complements running and testing the code instead of replacing them.
