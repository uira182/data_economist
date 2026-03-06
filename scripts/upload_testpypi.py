"""
Publica o pacote no Test PyPI (test.pypi.org), usando credenciais do .env.

O token no .env deve ser do Test PyPI: https://test.pypi.org/manage/account/token/

Uso (na raiz do projeto):
  pip install python-dotenv twine
  python scripts/upload_testpypi.py

Depois, para instalar a partir do Test PyPI:
  pip install --index-url https://test.pypi.org/simple/ data-economist
"""

import os
import subprocess
import sys


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Instale python-dotenv: pip install python-dotenv", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("TWINE_PASSWORD"):
        print("Defina TWINE_USERNAME e TWINE_PASSWORD no .env (token do Test PyPI).", file=sys.stderr)
        sys.exit(1)

    dist = os.path.join(root, "dist")
    if not os.path.isdir(dist) or not os.listdir(dist):
        print("Primeiro construa o pacote: python -m build", file=sys.stderr)
        sys.exit(1)

    # Upload para Test PyPI (--repository testpypi)
    code = subprocess.call([
        sys.executable, "-m", "twine", "upload",
        "--repository", "testpypi",
        "dist/*"
    ])
    sys.exit(code)


if __name__ == "__main__":
    main()
