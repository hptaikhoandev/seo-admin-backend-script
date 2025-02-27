#!/bin/bash
clear

# Load configurations
. /etc/wptt/.wptt.conf
if [[ $ngon_ngu = '' ]]; then
    ngon_ngu='vi'
fi
. /etc/wptt/lang/$ngon_ngu.sh

# Function to display the output in a formatted box
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

# Check if directory exists
VHOST_DIR="/etc/wptt/vhost"

if [[ ! -d "$VHOST_DIR" ]]; then
    echo ""
    exit 1
fi
# Get a list of all hidden .conf files
conf_files=($(ls -A "$VHOST_DIR" | grep -E '^\..*\.conf$'))

# Check if any .conf files exist
if [[ ${#conf_files[@]} -eq 0 ]]; then
    echo ""
    exit 0
fi

# Extract domain names from filenames
domain_list=$(printf "%s\n" "${conf_files[@]}" | sed 's/^\.//' | sed 's/.conf$//')

echo "$domain_list"

# If a specific argument is passed (e.g., for automation), call another script
check_menu_wptangtoc_active=$1
if [[ $check_menu_wptangtoc_active = "98" ]]; then
    . /etc/wptt/wptt-domain-main 1
fi
