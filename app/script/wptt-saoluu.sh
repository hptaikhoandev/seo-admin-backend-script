#!/bin/bash
# @author: Gia Tuấn
# @website: https://wptangtoc.com
# @email: giatuan@wptangtoc.com
# @since: 2022
echo ""
echo ""
echo ""
echo "========================================================================="
echo "|Sao lưu & khôi phục => Sao lưu website                                 |"
echo "========================================================================="
. /etc/wptt-user/echo-color
NAME=$1

# Nếu NAME rỗng, yêu cầu người dùng chọn tên miền
if [[ $NAME = '' ]]; then
  if ! . /etc/wptt/tenmien; then
    echo "Error: Không thể tải file cấu hình /etc/wptt/tenmien" >&2
    exit 1
  fi
  echo ""
  echo "Lựa chọn domain hoặc subdomain bạn muốn sao chép: "
  echo ""
  if ! lua_chon_NAME; then
    echo "Error: Không thể thực thi lua_chon_NAME" >&2
    exit 1
  fi
fi

# Kiểm tra nếu cả NAME và NAME2 tồn tại
pathcheck_name1="/etc/wptt/vhost/.$NAME.conf"

if [[ -f "$pathcheck_name1" ]]; then
  echo "Error: Tên miền $NAME đều tồn tại trên hệ thống" >&2
  exit 1
fi

# Kiểm tra nếu $NAME không hợp lệ hoặc không tồn tại
if [[ "$NAME" = "0" || "$NAME" = "" ]]; then
  echo "Error: Tên miền không hợp lệ hoặc không được cung cấp." >&2
  exit 1
fi

pathcheck="/etc/wptt/vhost/.$NAME.conf"
if [[ ! -f "$pathcheck" ]]; then
  echo "Error: Tên miền $NAME không tồn tại trên hệ thống này." >&2
  exit 1
fi

if [[ $NAME = "98" ]];then
NAME=""
fi

if [[ "$NAME" = "" ]]; then
    . /etc/wptt-user/tenmien
    lua_chon_NAME
fi

pathcheck="/usr/local/lsws/$NAME/backup-website"
before_optimize=$(du -hs $pathcheck | sed 's/\t//g'| cut -f1 -d '/')
times=$(date +%Hgio\_%d\_%m\_%Y)
. /etc/wptt/vhost/."$NAME".conf
cd /usr/local/lsws/"$NAME"/html

_runing "Sao lưu database website $NAME"

if [[ $sql_gz = '' ]];then
mariadb-dump -u "$DB_User_web" -p"$DB_Password_web" "$DB_Name_web" >/usr/local/lsws/$NAME/backup-website/$NAME$times.sql
fi


if [[ $sql_gz ]];then
mariadb-dump -u "$DB_User_web" -p"$DB_Password_web" "$DB_Name_web" | gzip >/usr/local/lsws/$NAME/backup-website/$NAME$times.sql.gz
fi


if [[ $sql_gz = '' ]];then
check_file_error_database=$(du -c /usr/local/lsws/$NAME/backup-website/$NAME$times.sql | awk '{print $1}' | sed '1d')
if (( $check_file_error_database < 10 ));then
tuanxacnhandb="0"
_runloi "Sao lưu database website $NAME"
echo "========================================================================="
echo "Sao lưu backup database không thành công."
echo "========================================================================="
rm -f /usr/local/lsws/$NAME/backup-website/$NAME$times.sql
fi
fi


if [[ $sql_gz ]];then
check_file_error_database=$(du -c /usr/local/lsws/$NAME/backup-website/$NAME$times.sql.gz | awk '{print $1}' | sed '1d')
if (( $check_file_error_database < 10 ));then
tuanxacnhandb="0"
_runloi "Sao lưu database website $NAME"
echo "========================================================================="
echo "Sao lưu backup database không thành công."
echo "========================================================================="
rm -f /usr/local/lsws/$NAME/backup-website/$NAME$times.sql.gz
fi
fi


if [[ -f /usr/local/lsws/$NAME/backup-website/$NAME$times.sql || -f /usr/local/lsws/$NAME/backup-website/$NAME$times.sql.gz ]];then
_rundone "Sao lưu database website $NAME"
tuanxacnhandb="1"
else
_runloi "Sao lưu database website $NAME"
fi


_runing "Sao lưu mã nguồn website $NAME"
echo ''
cd /usr/local/lsws/"$NAME"/html && zip -r /usr/local/lsws/$NAME/backup-website/$NAME$times.zip * -x "wp-content/ai1wm-backups/*" -x "wp-content/cache/*" -x "wp-content/updraft/*" -x "wp-content/ai1wm-backups/*" -x "error_log" -x "wp-content/debug.log" -x "wp-content/uploads/backupbuddy_backups/*" -x "wp-content/backups-dup-pro/*"

if [[ -f /usr/local/lsws/$NAME/backup-website/$NAME$times.zip ]];then
_rundone "Sao lưu mã nguồn website $NAME"
tuanxacnhan="1"
else
_runloi "Sao lưu mã nguồn website $NAME"
fi