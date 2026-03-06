"""
Publica o pacote no Test PyPI (test.pypi.org), usando credenciais do .env.

No .env use TWINE_USERNAME=__token__ e TWINE_TEST_PASSWORD=<token do Test PyPI>.
O script usa TWINE_TEST_PASSWORD para o upload (TWINE_PASSWORD fica para o pypi.org).

Registo do token Test PyPI: https://test.pypi.org/manage/account/token/

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

    test_password = os.getenv("TWINE_TEST_PASSWORD")
    if not test_password or not str(test_password).strip():
        print(
            "Defina TWINE_USERNAME=__token__ e TWINE_TEST_PASSWORD no .env (token do Test PyPI).",
            file=sys.stderr,
        )
        sys.exit(1)

    dist = os.path.join(root, "dist")
    if not os.path.isdir(dist) or not os.listdir(dist):
        print("Primeiro construa o pacote: python -m build", file=sys.stderr)
        sys.exit(1)

    # Upload apenas a versão mais recente (evita 403 ao reenviar versões já existentes)
    import re
    prefix = "data_economist-"
    versions = []
    for f in os.listdir(dist):
        if f.startswith(prefix) and (f.endswith(".whl") or f.endswith(".tar.gz")):
            m = re.match(r"data_economist-(\d+\.\d+\.\d+)(?:-.+)?\.(?:whl|tar\.gz)$", f)
            if m:
                versions.append((m.group(1), os.path.join(dist, f)))
    if not versions:
        print("Nenhum ficheiro data_economist-*.whl ou *.tar.gz em dist/", file=sys.stderr)
        sys.exit(1)
    versions.sort(key=lambda x: [int(u) for u in x[0].split(".")], reverse=True)
    latest_ver = versions[0][0]
    latest_files = [p for v, p in versions if v == latest_ver]
    print(f"A enviar versão {latest_ver}: {[os.path.basename(p) for p in latest_files]}")

    # Twine usa TWINE_PASSWORD; para Test PyPI usamos TWINE_TEST_PASSWORD
    os.environ["TWINE_PASSWORD"] = str(test_password).strip()

    code = subprocess.call([
        sys.executable, "-m", "twine", "upload",
        "--repository", "testpypi",
    ] + latest_files)
    sys.exit(code)


if __name__ == "__main__":
    main()
