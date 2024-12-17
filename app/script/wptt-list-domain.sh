#!/bin/bash
clear

. /etc/wptt/.wptt.conf
if [[ $ngon_ngu = '' ]]; then
    ngon_ngu='vi'
fi
. /etc/wptt/lang/$ngon_ngu.sh

function box_out() {
  local s=("$@") b w
  for l in "${s[@]}"; do
    ((w<${#l})) && { b="$l"; w="${#l}"; }
  done
  tput setaf 3
  echo " -${b//?/-}-
| ${b//?/ } |"
  for l in "${s[@]}"; do
    printf '| %s%*s%s |\n' "$(tput setaf 4)" "-$w" "$l" "$(tput setaf 3)"
  done
  echo "| ${b//?/ } |
 -${b//?/-}-"
  tput sgr 0
}

so_luong_website=$(ls -A /etc/wptt/vhost | grep '.conf' | wc -l)

check_menu_wptangtoc_active=$1
if [[ $check_menu_wptangtoc_active = "98" ]]; then
    . /etc/wptt/wptt-domain-main 1
fi

# Xuất giá trị so_luong_website
echo "$so_luong_website" >&1
