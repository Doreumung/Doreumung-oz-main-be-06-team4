set -eo pipefail  #실패하면 더이상 진행하지 않겠다
# 실패는 어떻게 알 수 있나요? 명령어를 실행하면 모든 명령어는 exit code 를 실행합니다 (리눅스 규칙)
# exit code 는 interger 인데 이게 0이 아닌 모든 같은 비정상 종료

COLOR_GREEN=`tput setaf 2;`
COLOR_NC=`tput sgr0;` # No Color

echo "Starting black"
poetry run black .
echo "OK"

echo "Starting isort"
poetry run isort .
echo "OK"

echo "Starting mypy"
poetry run mypy .
echo "OK"
