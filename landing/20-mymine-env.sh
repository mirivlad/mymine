#!/bin/sh
set -eu

: "${AUTH_BASE_URL:?AUTH_BASE_URL is required}"
: "${MC_ADDRESS:?MC_ADDRESS is required}"
: "${MC_VERSION:=26.2}"
: "${SERVER_NAME:=MyMine}"
: "${HMCL_VERSION:=3.16.3}"
: "${MAP_URL:=/map/}"
: "${VERIFY_MINECRAFT_OWNERSHIP:=true}"
: "${LANDING_TEMPLATE:=adventure}"
: "${LANDING_HERO_IMAGE:=/assets/voxel-world.webp}"
: "${LANDING_GALLERY_IMAGE_1:=/assets/isometric-world.webp}"
: "${LANDING_GALLERY_IMAGE_2:=/assets/bluemap.webp}"
: "${LANDING_GALLERY_IMAGE_3:=/assets/voxel-world.webp}"

case "$LANDING_TEMPLATE" in
  showcase|adventure|atlas|modern|terminal|classic)
    TEMPLATE="/opt/mymine/templates/${LANDING_TEMPLATE}.html.template"
    ;;
  *)
    echo "LANDING_TEMPLATE must be one of: showcase, adventure, atlas, modern, terminal, classic" >&2
    exit 1
    ;;
esac

case "$VERIFY_MINECRAFT_OWNERSHIP" in
  true)
    OWNERSHIP_MODE_LABEL="Проверка владения включена"
    OWNERSHIP_LEAD="Аккаунт MyMine используется для постоянного входа. При регистрации нужно один раз подтвердить владение существующим профилем Minecraft; после проверки постоянная Microsoft-авторизация в MyMine Launcher не требуется."
    OWNERSHIP_NOTICE_TITLE="При регистрации потребуется профиль Minecraft"
    OWNERSHIP_NOTICE_TEXT="Сервер работает в рекомендованном режиме: Drasl импортирует существующий Minecraft-профиль и подтверждает владение через временный skin challenge. После этого вход выполняется через отдельный аккаунт MyMine."
    OWNERSHIP_STEP_TEXT="Создай аккаунт MyMine, импортировав существующий Minecraft-профиль. Drasl покажет skin challenge для подтверждения владения."
    OWNERSHIP_STEP_BADGE="проверка профиля"
    OWNERSHIP_FAQ="Да, для первичной регистрации требуется существующий Minecraft-профиль. После подтверждения MyMine использует собственную авторизацию, поэтому вход через Microsoft при каждом запуске не нужен."
    ;;
  false)
    OWNERSHIP_MODE_LABEL="Независимая регистрация"
    OWNERSHIP_LEAD="MyMine работает с полностью самостоятельной Drasl-авторизацией и не выполняет автоматическую проверку владения Minecraft. Политику доступа и соблюдение применимых правил определяет администратор сервера."
    OWNERSHIP_NOTICE_TITLE="Проверка владения отключена владельцем сервера"
    OWNERSHIP_NOTICE_TEXT="Этот сервер разрешает независимую регистрацию без проверки существующего Minecraft-профиля. MyMine не определяет наличие приобретённой копии игры; ответственность за политику доступа и соблюдение Minecraft EULA/Usage Guidelines лежит на операторе сервера."
    OWNERSHIP_STEP_TEXT="Создай отдельный аккаунт MyMine на сервере авторизации. Проверка существующего Minecraft-профиля на этой установке отключена."
    OWNERSHIP_STEP_BADGE="автономный режим"
    OWNERSHIP_FAQ="Нет, эта установка MyMine использует независимую регистрацию. Проверка владения Minecraft отключена администратором сервера; это не является заявлением о праве использовать игру без действующей лицензии."
    ;;
  *)
    echo "VERIFY_MINECRAFT_OWNERSHIP must be true or false" >&2
    exit 1
    ;;
esac

export AUTH_BASE_URL MC_ADDRESS MC_VERSION SERVER_NAME HMCL_VERSION MAP_URL VERIFY_MINECRAFT_OWNERSHIP LANDING_TEMPLATE
export LANDING_HERO_IMAGE LANDING_GALLERY_IMAGE_1 LANDING_GALLERY_IMAGE_2 LANDING_GALLERY_IMAGE_3
export OWNERSHIP_MODE_LABEL OWNERSHIP_LEAD OWNERSHIP_NOTICE_TITLE OWNERSHIP_NOTICE_TEXT
export OWNERSHIP_STEP_TEXT OWNERSHIP_STEP_BADGE OWNERSHIP_FAQ

envsubst '${AUTH_BASE_URL} ${MC_ADDRESS} ${MC_VERSION} ${SERVER_NAME} ${HMCL_VERSION} ${MAP_URL} ${VERIFY_MINECRAFT_OWNERSHIP} ${LANDING_TEMPLATE} ${LANDING_HERO_IMAGE} ${LANDING_GALLERY_IMAGE_1} ${LANDING_GALLERY_IMAGE_2} ${LANDING_GALLERY_IMAGE_3} ${OWNERSHIP_MODE_LABEL} ${OWNERSHIP_LEAD} ${OWNERSHIP_NOTICE_TITLE} ${OWNERSHIP_NOTICE_TEXT} ${OWNERSHIP_STEP_TEXT} ${OWNERSHIP_STEP_BADGE} ${OWNERSHIP_FAQ}' \
  < "$TEMPLATE" \
  > /usr/share/nginx/html/index.html

AUTH_URL="${AUTH_BASE_URL%/}/"
printf '{\n  "urls": ["%s"]\n}\n' "$AUTH_URL" \
  > /usr/share/nginx/html/authlib-injectors.json

printf '{"minecraft":"%s","auth":"%s","version":"%s","map":"%s","ownershipVerification":%s,"template":"%s"}\n' \
  "$MC_ADDRESS" "$AUTH_URL" "$MC_VERSION" "$MAP_URL" "$VERIFY_MINECRAFT_OWNERSHIP" "$LANDING_TEMPLATE" \
  > /usr/share/nginx/html/server.json
