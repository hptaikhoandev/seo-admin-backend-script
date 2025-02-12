#!/bin/bash
# @author: Hex
# @since: 2024
. /etc/wptt/.wptt.conf

#configurations
idusername="admin"
mypassword="hp@123@a"
emailwp="ad@gmail.com"
link_source_wp="https://devmkt.s3.amazonaws.com/latest.tar.gz"

#crontab declaration
phut=4320 #60*24*3 (3 ngày)
days_delete_backup_files=7 # số ngày xóa delete trên google drive

# Sử dụng vòng lặp for để đọc từng dòng trong file
# Nhận domain từ tham số đầu vào
domain=$1

# Kiểm tra nếu biến domain rỗng
if [[ -z "$domain" ]]; then
    echo "Lỗi: Domain không được để trống." >&2
    exit 1
fi

# Đường dẫn tới file cấu hình
path="/etc/wptt/vhost/.$domain.conf"

# Kiểm tra nếu file cấu hình tồn tại
if [[ -f "$path" ]]; then
    echo "$domain đã tồn tại." >&2
    exit 0
fi

# Tạo tên user từ domain
USER=${domain//[-._]/wp}

# Nạp file cấu hình chung
if ! . /etc/wptt/.wptt.conf; then
    echo "Không thể tải file cấu hình /etc/wptt/.wptt.conf." >&2
    exit 1
fi

# Thực hiện các hành động tiếp theo...
echo "Domain $domain hợp lệ và chưa tồn tại, tiếp tục xử lý..."

work_cpucore='1024'
cpucore=$(grep -c ^processor /proc/cpuinfo)
max_client=$(expr $work_cpucore \* $cpucore \* 2)
max_client_max=$(expr $work_cpucore \* $cpucore \* 3)
max_client_php=$(expr $work_cpucore \* $cpucore \/ 8)
tong_ram_byte=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
rong_ram_mb=$(echo "scale=0;${tong_ram_byte}/1024" | bc)

gioi_han_tien_trinh_bao_loi_503=$(expr $max_client \/ 8)

if [[ "$rong_ram_mb" = "" ]]; then
    rong_ram_mb="2048"
fi
# echo "Thêm $domain vào hệ thống"

# Giới hạn số ký tự tối đa cho user trong Linux là 32
check_ky_tu=$(echo $USER | wc -c)
if (( $check_ky_tu > 32 ));then
    USER=$(echo $USER | cut -c 1-30)
fi
# Tạo user và thư mục tương ứng
useradd -m -d /usr/local/lsws/$domain -s /sbin/nologin $USER >/dev/null 2>&1
if [[ $(cat /etc/passwd | cut -f1 -d ':' | grep -w $USER) = '' ]];then
    random=$(date +%s | sha256sum | base64 | head -c 2)
    echo "random: $random"
fi

version=$(curl -s https://wptangtoc.com/share/version-wptangtoc-ols.txt?domain-them=$domain)
echo "virtualhost $domain {
vhRoot                  /usr/local/lsws/$domain/
configFile              /usr/local/lsws/conf/vhosts/$domain/$domain.conf
allowSymbolLink         1
enableScript            1
restrained              1
maxKeepAliveReq         $max_client
setUIDMode              2
user                    $USER
group                   $USER
}" >>/usr/local/lsws/conf/httpd_config.conf
sed -i "/listener http/a map 		$domain $domain" /usr/local/lsws/conf/httpd_config.conf
mkdir /usr/local/lsws/conf/vhosts/"$domain"/
touch /usr/local/lsws/conf/vhosts/"$domain"/"$domain".conf

domainPHP=${domain//[-._]/}

echo "docRoot                   /usr/local/lsws/$domain/html
vhDomain                  $domain
enableGzip                1
cgroups                   0


index  {
useServer               0
indexFiles              index.html index.php
autoIndex               0
}

scripthandler  {
add                     lsapi:$domainPHP php
}

accessControl  {
allow                   *
}

lsrecaptcha  {
enabled                 1
type                    0
}

extprocessor $domainPHP {
type                    lsapi
address                 uds://tmp/lshttpd/$domainPHP.sock
maxConns                30
env                     PHP_LSAPI_CHILDREN=30
env                     LSAPI_AVOID_FORK=200M
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
location                /usr/local/lsws/$domain/html
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
/usr/local/lsws/$domain/html/.htaccess
}

vhssl  {
keyFile                 /etc/letsencrypt/live/$domain/privkey.pem
certFile                /etc/letsencrypt/live/$domain/cert.pem
certChain               0
CACertFile              /etc/letsencrypt/live/$domain/chain.pem
sslProtocol             24
renegProtection         1
sslSessionCache         1
sslSessionTickets       1
enableSpdy              15
enableQuic              1
enableStapling          1
ocspRespMaxAge          86400
ocspResponder           http://cert.int-x3.letsencrypt.org/
ocspCACerts             /etc/letsencrypt/live/$domain/chain.pem
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
storagePath /usr/local/lsws/$domain/luucache
enableCache         0
expireInSeconds     3600
enablePrivateCache  0
privateExpireInSeconds 3600
ls_enabled              1
}" >/usr/local/lsws/conf/vhosts/$domain/$domain.conf


#tuong thich ubuntu tuong thich nhom litespeed
if $(cat /etc/*release | grep -q "Ubuntu") ; then
tuong_thich_nhom_litespeed="nogroup"
else
tuong_thich_nhom_litespeed="nobody"
fi

chown -R lsadm:$tuong_thich_nhom_litespeed /usr/local/lsws/conf/vhosts/$domain
chmod -R 750 /usr/local/lsws/conf/vhosts/$domain
mkdir -p /usr/local/lsws/$domain
mkdir -p /usr/local/lsws/$domain/html
mkdir -p /usr/local/lsws/$domain/luucache
mkdir -p /usr/local/lsws/$domain/backup-website
mkdir -p /usr/local/backup-website/$domain
chmod 755 /usr/local/lsws/$domain
chmod 755 /usr/local/lsws/$domain/html
chmod 700 /usr/local/backup-website/$domain
chmod 700 /usr/local/lsws/$domain/backup-website
chown -R $USER:$USER /usr/local/lsws/$domain/html
chown -R $USER:$USER /usr/local/lsws/$domain/backup-website


if [[ ! -f /usr/local/lsws/"$domain"/html/.htaccess ]];then
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
# END WordPress' > /usr/local/lsws/"$domain"/html/.htaccess
fi

echo "Hoàn thành thêm domain $domain vào hệ thống"
sleep 0.4

name_db=${domain//[-._]/}
ramdom_db=$(
date +%s | sha256sum | base64 | head -c 18
echo
)
database=${name_db}_${ramdom_db}_dbname
username=${name_db}_${ramdom_db}_username
password=$(
date +%s | sha256sum | base64 | head -c 36
echo
)

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

echo "Thêm database website $domain"
mariadb -u $database_admin_username -p"$database_admin_password" -e "DROP DATABASE IF EXISTS ${database}"
mariadb -u $database_admin_username -p"$database_admin_password" -e "CREATE DATABASE IF NOT EXISTS ${database}"
mariadb -u $database_admin_username -p"$database_admin_password" -e "DROP USER IF EXISTS '${username}'@'localhost'"
mariadb -u $database_admin_username -p"$database_admin_password" -e "CREATE USER IF NOT EXISTS '${username}'@'localhost' IDENTIFIED BY '${password}'"
mariadb -u $database_admin_username -p"$database_admin_password" -e "GRANT ALL PRIVILEGES ON ${database}.* TO '${username}'@'localhost' WITH GRANT OPTION"
mariadb -u $database_admin_username -p"$database_admin_password" -e "FLUSH PRIVILEGES"
echo "Hoàn thành thêm database website $domain"

php_version=$(php -v |grep cli | cut -c 4-7| sed 's/ //g')

touch /etc/wptt/vhost/.$domain.conf
echo "DB_Name_web=$database
DB_User_web=$username
DB_Password_web=$password
Duong_Dan_thu_muc_web=/usr/local/lsws/$domain/html
User_name_vhost=$USER
phien_ban_php_domain=$php_version" >/etc/wptt/vhost/.$domain.conf

chown $USER:$USER /etc/wptt/vhost/.$domain.conf

mkdir -p /wptangtoc-ols
mkdir -p /wptangtoc-ols/$domain
mkdir -p /wptangtoc-ols/$domain/backup-website
ln -s /usr/local/lsws/$domain/html /wptangtoc-ols/$domain
ln -s /usr/local/backup-website/$domain/ /wptangtoc-ols/$domain/backup-website


#tao anh xa username
# mkdir -p /home/$USER/$domain
# ln -s /usr/local/lsws/$domain/html /home/$domain/public_html
# ln -s /usr/local/lsws/$domain/backup-website /home/$domain/backup-website

ln -s /usr/local/lsws/$domain /home/$domain


# add group
usermod -a -G wptangtoc-ols $USER

if [[ ! -f /usr/local/lsws/$domain/.bashrc ]];then
cp -rf /etc/skel/. /usr/local/lsws/$domain
fi

chown $USER:$USER /usr/local/lsws/$domain/.*

echo '[[ $- != *i* ]] && return' >> /usr/local/lsws/$domain/.bashrc
echo ". /etc/wptt-user/wptt-status" >> /usr/local/lsws/$domain/.bashrc
echo "alias 1='wptangtoc-user'" >> /usr/local/lsws/$domain/.bashrc
echo "alias 11='wptangtoc-user'" >> /usr/local/lsws/$domain/.bashrc

chown $USER:$USER /usr/local/lsws/"$domain"/html/.htaccess

# khong cho login quyen tai khoan trực tiếp chỉ sử dụng php exec
# usermod $USER -s /sbin/nologin
if [[ $(getent passwd $USER | cut -d: -f7) != "/sbin/nologin" ]]; then
    sudo usermod $USER -s /sbin/nologin
fi

if [[ -f /usr/local/lsws/$domain/html/index.html ]];then
sed -i "s/domain.com/$domain/g" /usr/local/lsws/"$domain"/html/index.html
chown $USER:$USER /usr/local/lsws/"$domain"/html/index.html
chmod 644 /usr/local/lsws/"$domain"/html/index.html
fi

php_ver_chon=${php_version_check//[-._]/}
sed -E -i "s/lsphp[0-9]+/lsphp$php_ver_chon/g" /usr/local/lsws/conf/vhosts/$domain/$domain.conf

/usr/local/lsws/bin/lswsctrl restart >/dev/null 2>&1
# Done tạo domain

# Cài đặt WP
. /etc/wptt/vhost/."$domain".conf
echo "Làm sạch dữ liệu của domain $domain"
cd /usr/local/lsws/"$domain"/html/
rm -rf /usr/local/lsws/"$domain"/html/*
sleep 0.4

echo "Tải mã nguồn WordPress"
wget -q $link_source_wp

if [[ ! -f latest.tar.gz ]];then
    echo "Chưa thể download mã nguồn WordPress vui lòng thử lại sau"
    echo "$domain" >> chua_cai_wp.txt
    return 2>/dev/null;exit
fi

echo "Đã tải mã nguồn WordPress"
echo "Đang giải nén mã nguồn WordPress"
tar --warning=no-unknown-keyword -zxf latest.tar.gz
mv wordpress/* /usr/local/lsws/"$domain"/html && rm -rf wordpress && rm -f latest.tar.gz
sleep 0.4

if [[ ! -f "/etc/letsencrypt/live/$domain/cert.pem" && ! -d /usr/local/lsws/$domain/ssl ]]; then
        ssl_check="http://"
    else
        ssl_check="https://"
fi

if [[ "$DB_Name_web" != "" ]]; then
    echo "Đang làm sạch database $domain"
    database="$DB_Name_web"
    mariadb -u $database_admin_username -p"$database_admin_password" -e "DROP DATABASE $DB_Name_web"
    mariadb -u $database_admin_username -p"$database_admin_password" -e "CREATE DATABASE IF NOT EXISTS $DB_Name_web"
    echo "Đã làm sạch toàn bộ database"
    sleep 0.4


if [[ ! -f /usr/local/bin/wp ]]; then
  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
  chmod +x wp-cli.phar
  mv wp-cli.phar /usr/local/bin/wp
fi

    tien_to_db=$(date +%s | sha256sum | base64 | head -c 6)

/usr/local/bin/wp core config \
    --dbname="$DB_Name_web" \
    --dbuser="$DB_User_web" \
    --dbpass="$DB_Password_web" \
    --dbhost=localhost \
    --dbprefix="${tien_to_db}"_ \
    --dbcharset='utf8mb4' \
    --dbcollate='utf8mb4_unicode_ci' \
    --allow-root \
    --extra-php <<PHP
define( 'WP_DEBUG_LOG', false );
define( 'WP_DEBUG_DISPLAY', false );
PHP
    
/usr/local/bin/wp core install \
    --url="${ssl_check}""${domain}" \
    --title="$domain" \
    --admin_user="$idusername" \
    --admin_password="$mypassword" \
    --admin_email="$emailwp" \
    --allow-root \
    --skip-email >/dev/null 2>&1

  echo '
# BEGIN WordPress
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress' >/usr/local/lsws/"$domain"/html/.htaccess

  /usr/local/bin/wp language core install vi --path=/usr/local/lsws/"$domain"/html --activate --allow-root >/dev/null 2>&1
  /usr/local/bin/wp option update timezone_string "Asia/Ho_Chi_Minh" --path=/usr/local/lsws/"$domain"/html --allow-root >/dev/null 2>&1
  /usr/local/bin/wp rewrite structure '/%postname%/' --path=/usr/local/lsws/"$domain"/html --allow-root >/dev/null 2>&1
    sleep 0.4

echo "Phân quyền website $domain"
chown -R "$User_name_vhost":"$User_name_vhost" /usr/local/lsws/"$domain"/html
# chmod -R 755 /usr/local/lsws/"$domain"/html
/usr/local/lsws/bin/lswsctrl restart >/dev/null 2>&1
  sleep 0.4
  fi
