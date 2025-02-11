#!/bin/bash
# @author: Gia Tuấn
# @website: https://wptangtoc.com
# @email: giatuan@wptangtoc.com
# @since: 2022
. /etc/wptt/echo-color
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

NAME=$1
NAME2=$2

if [[ $NAME = "98" ]];then
NAME=""
fi

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
pathcheck_name2="/etc/wptt/vhost/.$NAME2.conf"

if [[ -f "$pathcheck_name1" && -f "$pathcheck_name2" ]]; then
  echo "Error: Tên miền $NAME và $NAME2 đều đã tồn tại trên hệ thống" >&2
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


NAME_NGUON=$(echo $NAME)

if [[ $2 = '' ]]; then
read -p "Nhập domain hoặc subdomain bạn muốn thêm và sao chép vào
    (ví dụ: wptangtoc.com, abc.wptangtoc.com ...) [0=Thoát]: " NAME2
fi

if [ "$NAME2" = '' ]; then
  clear
  echo "Bạn chưa nhập tên miền domain." >&2  # In lỗi ra stderr
  exit 1
fi

if [[ "$NAME2" = "0" ]]; then
  clear
  echo "Thoát khỏi chương trình." >&2  # In thông báo thoát ra stderr nếu cần
    exit 1
fi

# Domain người dùng nhập sử dụng thêm space cách, sẽ báo không đúng định dạng
if [ $(echo $NAME2 | wc -w) -gt 1 ]; then
echo "ERROR: Domain nhập không đúng định dạng" >&2
exit 1
fi


#chuyển đổi viết hoa thành chữ thường điều kiện
NAME2=$(echo $NAME2 | tr '[:upper:]' '[:lower:]')


if [ "$NAME2" = "${NAME2/./}" ]; then
  clear
  echo "Domain ten mien nhap khong dung dinh dang."
  exit
fi

path2="/etc/wptt/vhost/.$NAME2.conf"
if [[ -f "$path2" ]]; then
  clear
  echo "Domain đã tồn tại trên hệ thống."
  echo "Muốn sử dụng tính năng này vui lòng xóa domain $NAME2 của bạn đi"
  echo
  exit
fi

#kiem tra phan loai bo http:// va www
if [[ $(echo $NAME2 | grep '://') ]];then
    NAME2=$(echo $NAME2 | cut -f3 -d '/')
fi

if [[ $(echo $NAME2 | grep '^www\.') ]];then
    NAME2=$(echo $NAME2 | sed 's/^www.//g')
fi


USER=${NAME2//[-._]/wp}

. /etc/wptt/.wptt.conf

work_cpucore='1024'
cpucore=$(grep -c ^processor /proc/cpuinfo)
max_client=$(expr $work_cpucore \* $cpucore \* 2)
max_client_max=$(expr $work_cpucore \* $cpucore \* 3)
max_client_php=$(expr $work_cpucore \* $cpucore \/ 8)
tong_ram_byte=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
rong_ram_mb=$(echo "scale=0;${tong_ram_byte}/1024" | bc)
gioi_han_tien_trinh_bao_loi_503=$(expr $max_client \/ 8)
_runing "Thêm domain $NAME2 vào hệ thống"

check_ky_tu=$(echo $USER | wc -c)
if (( $check_ky_tu > 32 ));then
	USER=$(echo $USER | cut -c 1-30)
fi

# useradd $USER -p -m -d /usr/local/lsws/$NAME2 >/dev/null 2>&1
useradd -p -m -d /usr/local/lsws/$NAME2 $USER >/dev/null 2>&1

if [[ $(cat /etc/passwd | cut -f1 -d ':' | grep -w $USER) = '' ]];then
	random=$(
	date +%s | sha256sum | base64 | head -c 2
	echo
)

USER=${NAME2//[-._]/$random}
USER=$(echo $USER | tr '[:upper:]' '[:lower:]')
check_ky_tu2=$(echo $USER | wc -c)
if (( $check_ky_tu2 > 32 ));then
	USER=$(echo $USER | cut -c 1-30)
fi
# useradd $USER -p -m -d /usr/local/lsws/$NAME2 >/dev/null 2>&1
useradd -p -m -d /usr/local/lsws/$NAME2 $USER >/dev/null 2>&1
fi


if [[ $(cat /etc/passwd | cut -f1 -d ':' | grep -w $USER) = '' ]];then
	_runloi "Thêm domain $NAME vào hệ thống"
	echoDo "Đã có lỗi vấn đề về hệ điều hành không thể tạo user mới"
	wptangtoc 1
	exit
fi


echo "virtualhost $NAME2 {
  vhRoot                  /usr/local/lsws/$NAME2/
  configFile              /usr/local/lsws/conf/vhosts/$NAME2/$NAME2.conf
  allowSymbolLink         1
  enableScript            1
  restrained              1
  maxKeepAliveReq         $max_client
  setUIDMode              2
  user                    $USER
  group                   $USER
}" >>/usr/local/lsws/conf/httpd_config.conf
sed -i "/listener http/a map 		$NAME2 $NAME2" /usr/local/lsws/conf/httpd_config.conf
mkdir /usr/local/lsws/conf/vhosts/$NAME2/
touch /usr/local/lsws/conf/vhosts/$NAME2/$NAME2.conf
NAMEPHP=${NAME2//[-._]/}
echo "docRoot                   /usr/local/lsws/$NAME2/html
vhDomain                  $NAME2
enableGzip                1
cgroups                   0


index  {
  useServer               0
  indexFiles              index.html index.php
  autoIndex               0
}

scripthandler  {
  add                     lsapi:$NAMEPHP php
}

accessControl  {
  allow                   *
}

lsrecaptcha  {
  enabled                 1
  type                    0
}

extprocessor $NAMEPHP {
  type                    lsapi
  address                 uds://tmp/lshttpd/$NAMEPHP.sock
  maxConns                30
  env                     PHP_LSAPI_CHILDREN=30
  initTimeout             60
  retryTimeout            0
  pcKeepAliveTimeout      5
  respBuffer              0
  autoStart               1
  path                    /usr/local/lsws/lsphp74/bin/lsphp
  backlog                 100
  instances               1
  extUser                 $USER
  extGroup                $USER
  runOnStartUp            2
  priority                0
  memSoftLimit            ${rong_ram_mb}M
  memHardLimit            ${rong_ram_mb}M
  procSoftLimit           $gioi_han_tien_trinh_bao_loi_503
  procHardLimit           $gioi_han_tien_trinh_bao_loi_503
}

context / {
  location                /usr/local/lsws/$NAME2/html
  allowBrowse             1
  extraHeaders            <<<END_extraHeaders
X-XSS-Protection 1;mode=block
X-Frame-Options SAMEORIGIN
Referrer-Policy strict-origin-when-cross-origin
X-Content-Type-Options nosniff
X-Powered-By WPTangTocOLS
permissions-policy accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()
  END_extraHeaders


  rewrite  {

  }
  addDefaultCharset       off

  phpIniOverride  {

  }
}

rewrite  {
  enable                  1
  autoLoadHtaccess        1
/usr/local/lsws/$NAME2/html/.htaccess
}

vhssl  {
  keyFile                 /etc/letsencrypt/live/$NAME2/privkey.pem
  certFile                /etc/letsencrypt/live/$NAME2/cert.pem
  certChain               0
  CACertFile              /etc/letsencrypt/live/$NAME2/chain.pem
  sslProtocol             24
  renegProtection         1
  sslSessionCache         1
  sslSessionTickets       1
  enableSpdy              15
  enableQuic              1
  enableStapling          1
  ocspRespMaxAge          86400
  ocspResponder           http://cert.int-x3.letsencrypt.org/
  ocspCACerts             /etc/letsencrypt/live/$NAME2/chain.pem
}

module cache {
checkPrivateCache   1
checkPublicCache    1
maxCacheObjSize     10000000
maxStaleAge         200
qsCache             1
reqCookieCache      1
respCookieCache     1
ignoreReqCacheCtrl  1
ignoreRespCacheCtrl 0
storagePath /usr/local/lsws/$NAME2/luucache
enableCache         0
expireInSeconds     3600
enablePrivateCache  0
privateExpireInSeconds 3600
  ls_enabled              1
}" >/usr/local/lsws/conf/vhosts/"$NAME2"/"$NAME2".conf

#tuong thich ubuntu tuong thich nhom litespeed
if $(cat /etc/*release | grep -q "Ubuntu") ; then
tuong_thich_nhom_litespeed="nogroup"
else
tuong_thich_nhom_litespeed="nobody"
fi

chown -R lsadm:$tuong_thich_nhom_litespeed /usr/local/lsws/conf/vhosts/"$NAME2"
chmod -R 750 /usr/local/lsws/conf/vhosts/"$NAME2"

mkdir -p /usr/local/lsws/"$NAME2"
mkdir -p /usr/local/lsws/"$NAME2"/html
mkdir -p /usr/local/lsws/"$NAME2"/backup-website
mkdir -p /usr/local/lsws/"$NAME2"/luucache
chmod 755 /usr/local/lsws/"$NAME2"/
chmod 755 /usr/local/lsws/"$NAME2"/html
chmod 700 /usr/local/lsws/"$NAME2"/backup-website


chown -R "$USER":"$USER" /usr/local/lsws/"$NAME2"/html

touch /usr/local/lsws/"$NAME2"/html/.htaccess

echo '# BEGIN WordPress
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress' > /usr/local/lsws/"$NAME2"/html/.htaccess

_rundone "Thêm domain $NAME2 vào hệ thống"

name_db=${NAME2//[-._]/}
ramdom_db=$(date +%s | sha256sum | base64 | head -c 18 ; echo)
database=${name_db}_${ramdom_db}_dbname
username=${name_db}_${ramdom_db}_username
password=$(date +%s | sha256sum | base64 | head -c 36 ; echo)


#toi ky tu database la 64
check_ky_tu_database_name=$(echo $database | wc -c)
if (( $check_ky_tu_database_name > 60 ));then
	database=$(echo $database | cut -c 1-60)
fi

#toi ky tu database la 64
check_ky_tu_user_name=$(echo $username | wc -c)
if (( $check_ky_tu_user_name > 60 ));then
	username=$(echo $username | cut -c 1-60)
fi
_runing "Thêm database mới cho website $NAME2"
mariadb -u "$database_admin_username" -p"$database_admin_password" -e "DROP DATABASE IF EXISTS ${database}"
mariadb -u "$database_admin_username" -p"$database_admin_password" -e "CREATE DATABASE IF NOT EXISTS ${database}"
mariadb -u "$database_admin_username" -p"$database_admin_password" -e "DROP USER IF EXISTS '${username}'@'localhost'"
mariadb -u "$database_admin_username" -p"$database_admin_password" -e "CREATE USER IF NOT EXISTS '${username}'@'localhost' IDENTIFIED BY '${password}'"
mariadb -u "$database_admin_username" -p"$database_admin_password" -e "GRANT ALL PRIVILEGES ON ${database}.* TO '${username}'@'localhost' WITH GRANT OPTION"
mariadb -u "$database_admin_username" -p"$database_admin_password" -e "FLUSH PRIVILEGES"
_rundone "Thêm database mới cho website $NAME2"

# php_ver_chon=${php_version_check//[-._]/}
# sed -E -i "s/lsphp[0-9]+/lsphp$php_ver_chon/g" /usr/local/lsws/conf/vhosts/$NAME2/$NAME2.conf
_runing "Sao chép website $NAME sang website $NAME2"
. /etc/wptt/vhost/."$NAME".conf

#config phiên bản php của website gốc
if [[ $phien_ban_php_domain = '' ]];then
phien_ban_php_domain=$(php -v |grep cli | cut -c 4-7| sed 's/ //g')
fi
php_ver_chon=${phien_ban_php_domain//[-._]/}

sed -E -i "s/lsphp[0-9]+/lsphp$php_ver_chon/g" /usr/local/lsws/conf/vhosts/$NAME2/$NAME2.conf

mkdir -p "/usr/local/lsws/database"
file_sql=${database}.sql
duong_dan_thu_muc="/usr/local/lsws/database/$file_sql"
mariadb-dump -u "$database_admin_username" -p"$database_admin_password" "$DB_Name_web" > "$duong_dan_thu_muc"
sleep 1
# Replace all occurrences of domainA.com with domainB.com in the SQL dump file
sed -E -i "s/$NAME/$NAME2/g" "$duong_dan_thu_muc"
#check version wptt
if command -v mariadb &> /dev/null; then
    mariadb -h localhost -u "$database_admin_username" -p"$database_admin_password" "$database" < "$duong_dan_thu_muc"
elif command -v mysql &> /dev/null; then
    mysql -h localhost -u "$database_admin_username" -p"$database_admin_password" "$database" < "$duong_dan_thu_muc"
fi

rm -f "$duong_dan_thu_muc"
duong_dan_nguon_cu="/usr/local/lsws/$NAME/html"
duong_dan_nguon_moi21="/usr/local/lsws/$NAME2"
duong_dan_nguon_moi="/usr/local/lsws/$NAME2/html"

if ! cp -r "$duong_dan_nguon_cu" "$duong_dan_nguon_moi21"; then
  echo "Copy thất bại. Dừng script." >&2
  exit 1
fi

sed -i "/DB_HOST/s/'[^']*'/'localhost'/2" "/usr/local/lsws/$NAME2/html/wp-config.php"
sed -i "/DB_NAME/s/'[^']*'/'$database'/2" "/usr/local/lsws/$NAME2/html/wp-config.php"
sed -i "/DB_USER/s/'[^']*'/'$username'/2" "/usr/local/lsws/$NAME2/html/wp-config.php"
sed -i "/DB_PASSWORD/s/'[^']*'/'$password'/2" "/usr/local/lsws/$NAME2/html/wp-config.php"
cd /usr/local/lsws/"$NAME2"/html/
wp search-replace "//${NAME}" "//${NAME2}" --path="$duong_dan_nguon_moi" --allow-root >/dev/null 2>&1
wp cache flush --allow-root --path="$duong_dan_nguon_moi" >/dev/null 2>&1
wp rewrite flush --allow-root --path="$duong_dan_nguon_moi" >/dev/null 2>&1
checkplugin="/usr/local/lsws/$NAME2/html/wp-content/plugins/litespeed-cache"
if [[ -d $checkplugin ]]; then
  wp litespeed-purge all --allow-root --path="$duong_dan_nguon_moi" >/dev/null 2>&1
fi

chown -R $USER:$USER /usr/local/lsws/$NAME2/html
chown -R $USER:$USER /usr/local/lsws/$NAME2/backup-website

if [[ ! -f /usr/local/lsws/$NAME2/.bashrc ]];then
cp -rf /etc/skel/. /usr/local/lsws/$NAME2
fi


chown $USER:$USER /usr/local/lsws/$NAME2/.*

chmod 700 /usr/local/lsws/$NAME2/backup-website


mkdir -p /usr/local/backup-website/"$NAME2"

mkdir -p /wptangtoc-ols
mkdir -p /wptangtoc-ols/"$NAME2"
mkdir -p /wptangtoc-ols/"$NAME2"/backup-website

ln -s /usr/local/lsws/"$NAME2"/html /wptangtoc-ols/"$NAME2"
ln -s /usr/local/backup-website/"$NAME2"/ /wptangtoc-ols/"$NAME2"/backup-website

#anh xa thu muc home
ln -s /usr/local/lsws/$NAME2 /home/$NAME2


if [[ -f /usr/local/lsws/$NAME2/html/wp-content/db.php ]];then
rm -f /usr/local/lsws/$NAME2/html/wp-content/db.php
fi


usermod -a -G wptangtoc-ols $USER

# khong cho login quyen tai khoan trực tiếp chỉ sử dụng để làm sử dụng php exec
usermod $USER -s /sbin/nologin

# echo '[[ $- != *i* ]] && return' >> /home/$USER/.bashrc
# echo ". /etc/wptt-user/wptt-status" >> /home/$USER/.bashrc
# echo "alias 1='wptangtoc-user'" >> /home/$USER/.bashrc
# echo "alias 11='wptangtoc-user'" >> /home/$USER/.bashrc

echo '[[ $- != *i* ]] && return' >> /usr/local/lsws/$NAME2/.bashrc
echo ". /etc/wptt-user/wptt-status" >> /usr/local/lsws/$NAME2/.bashrc
echo "alias 1='wptangtoc-user'" >> /usr/local/lsws/$NAME2/.bashrc
echo "alias 11='wptangtoc-user'" >> /usr/local/lsws/$NAME2/.bashrc


# mkdir -p /home/$USER/$NAME2
# ln -s /usr/local/lsws/$NAME2/html /home/$USER/$NAME2/public_html
# ln -s /usr/local/lsws/$NAME2/backup-website /home/$USER/$NAME2/backup-website


if [[ -f /usr/local/lsws/$NAME2/html/wp-config.php ]];then
sed -i "/WP_SITEURL/d" /usr/local/lsws/$NAME2/html/wp-config.php
sed -i "/WP_HOME/d" /usr/local/lsws/$NAME2/html/wp-config.php
if [[ -d /usr/local/lsws/$NAME2/html/wp-content/cache ]];then
rm -rf /usr/local/lsws/$NAME2/html/wp-content/cache
fi
fi


/usr/local/lsws/bin/lswsctrl restart >/dev/null 2>&1


php_version=$(php -v |grep cli | cut -c 4-7| sed 's/ //g')

touch /etc/wptt/vhost/."$NAME2".conf
echo "DB_Name_web=$database
DB_User_web=$username
DB_Password_web=$password
Duong_Dan_thu_muc_web=/usr/local/lsws/$NAME2/html
User_name_vhost=$USER
phien_ban_php_domain=$phien_ban_php_domain" >/etc/wptt/vhost/."$NAME2".conf
# _runing "Xóa cache"
. /etc/wptt/cache/wptt-xoacache $NAME2 >/dev/null 2>&1
# _rundone "Xóa cache"
. /etc/wptt/wordpress/thay-salt $NAME2 >/dev/null 2>&1
_rundone "Sao chép website $NAME_NGUON sang website $NAME2"


echo "==================================================================="
echo "Hoàn tất sao chép $NAME_NGUON sang $NAME2               "
echo "==================================================================="
echo "==================================================================="
echo "Disk  : $(df -BG | awk '$NF=="/"{printf "%d/%dGB (%s)\n", $3,$2,$5}')                        "
echo "RAM   : $(free -m | awk 'NR==2{printf "%s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }')                         "
echo "==================================================================="
echo "DB_Name:  $database                                "
echo "DB_User:  $username                                "
echo "DB_Password:  $password				 "
echo "duong dan thu muc website: /usr/local/lsws/$NAME2/html              "
echo "moi thong tin tai khoan da duoc luu tru:  /etc/wptt/vhost/.$NAME2.conf    "
echo "==================================================================="
echo "Phần mềm phát triển bởi: Gia Tuấn"
echo "==================================================================="
checkdns=$(host $NAME2 | grep -Eo -m 1 '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
if [[ "$checkdns" = "" ]]; then
  checkdns=$(nslookup $NAME2 | grep Address | cut -f5 | grep -Eo -m 1 '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
fi

ip=$(curl -s myip.directadmin.com)
if [[ "$ip" = "" ]]; then
  ip=$(curl -s ifconfig.me)
fi

if [[ "$checkdns" != "$ip" ]]; then
  if [[ "$checkdns" = "" ]]; then
      echo "Tên miền $NAME2 chưa được trỏ IP, giá trị IP của $NAME là không có giá trị nào, bạn vui lòng trỏ IP về $ip"
  else
      echo "Hãy trỏ DNS domain $NAME2: $checkdns thành $ip để tận hưởng thành quả"
  fi
fi

check_menu_wptangtoc_active=$1
if [[ $check_menu_wptangtoc_active = "98" ]];then
wptangtoc 1
fi