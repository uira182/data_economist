"""
Script auxiliar para publicar no PyPI carregando credenciais do .env.

Uso (na raiz do projeto):
  pip install python-dotenv
  python scripts/upload_pypi.py

Requisito: ficheiro .env na raiz com TWINE_USERNAME e TWINE_PASSWORD.
Ver config/README.md para como configurar o token.
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
        print("Defina TWINE_USERNAME e TWINE_PASSWORD no .env. Ver config/README.md", file=sys.stderr)
        sys.exit(1)

    dist = os.path.join(root, "dist")
    if not os.path.isdir(dist) or not os.listdir(dist):
        print("Primeiro construa o pacote: python -m build", file=sys.stderr)
        sys.exit(1)

    # Upload para PyPI (produção)
    code = subprocess.call([sys.executable, "-m", "twine", "upload", "dist/*"])
    sys.exit(code)


if __name__ == "__main__":
    main()
