# #!/bin/bash
# # @author: Gia Tuấn
# # @website: https://wptangtoc.com
# # @email: giatuan@wptangtoc.com
# # @since: 2022
# NAME=$1
# if [[ $NAME = "" ]];then 
# echo ""
# echo ""
# echo ""
# echo "========================================================================="
# echo "|Reinstall WordPress Clean mã nguồn		                              |"
# echo "========================================================================="
# . /etc/wptt/tenmien
# echo ""
# echo ""
# echo "Lựa chọn website Reinstall WordPress: "
# echo ""
# lua_chon_NAME
# fi


# rm -rf /usr/local/lsws/$NAME/html/wp-admin
# rm -rf /usr/local/lsws/$NAME/html/wp-includes

# file=(
# 	php.ini
# 	user.ini
# )

# for deletefile in ${file[@]}; do
#     rm -f /usr/local/lsws/$NAME/html/$deletefile
# done


# #xoá toàn bộ php thư mục goc ngoai tru wp-config.php
# mv /usr/local/lsws/$NAME/html/wp-config.php /usr/local/lsws/$NAME/html/wp-content

# if [[ -d /usr/local/lsws/$NAME/html/wp-content/plugins/devvn-quick-search ]];then
# mv /usr/local/lsws/$NAME/html/search.php /usr/local/lsws/$NAME/html/wp-content
# fi

# cd /usr/local/lsws/$NAME/html && rm -f *.php
# mv /usr/local/lsws/$NAME/html/wp-content/wp-config.php /usr/local/lsws/$NAME/html

# if [[ -d /usr/local/lsws/$NAME/html/wp-content/plugins/devvn-quick-search ]];then
# mv /usr/local/lsws/$NAME/html/wp-content/search.php /usr/local/lsws/$NAME/html
# fi



# check_zip_php=$(php -m | grep 'zip')
# if [[ $check_zip_php = '' ]];then
# phien_ban_php_cli_hien_tai=$(php -v |grep cli | cut -c 4-7| sed 's/ //g')
# . /etc/wptt/php/install-php-zip "$phien_ban_php_cli_hien_tai" >/dev/null 2>&1
# fi

# check_zip_php=$(php -m | grep 'zip')
# if [[ $check_zip_php = '' ]];then
# echo "Thiếu thư viện php extension zip để thực thi câu lệnh"
# exit
# fi

# wp core download --skip-content --force --allow-root --path=/usr/local/lsws/$NAME/html 2>/dev/null
# wp core update-db --allow-root --path=/usr/local/lsws/$NAME/html 2>/dev/null
# wp plugin install $(wp plugin list --field=name --allow-root --path=/usr/local/lsws/$NAME/html) --force --allow-root 2>/dev/null --path=/usr/local/lsws/$NAME/html
# wp theme install $(wp theme list --field=name --path=/usr/local/lsws/$NAME/html --allow-root) --force --allow-root 2>/dev/null --path=/usr/local/lsws/$NAME/html

# if [[ -d /usr/local/lsws/$NAME/html/wp-content/cache ]];then
# 	rm -rf /usr/local/lsws/$NAME/html/wp-content/cache
# fi

# if [[ -d /usr/local/lsws/$NAME/luucache ]];then
# 	rm -rf /usr/local/lsws/$NAME/luucache
# fi

# path="/usr/local/lsws/$NAME/html"
# wp cron event list --allow-root --path=$path 2>/dev/null | grep 'vtpost_login_daily' | awk '{ print $1 }' | xargs --replace=% wp cron event delete % --allow-root --path=$path 2>/dev/null


# checkchild=$(wp theme list --path=$path --allow-root | grep -c 'parent')
# if [[ "$checkchild" != "1" ]]; then
# 	name_theme=$(wp theme status --path=$path --allow-root | grep 'A' | head -1 | awk '{print $2}')
# 	if [[ -f $path/wp-content/themes/$name_theme/index.php ]];then
# 		rm -f $path/wp-content/themes/$name_theme/index.php
# 	fi
# fi

# find $path/wp-content/uploads -type f -name "index.php" -delete
# echo '<?php' > $path/wp-content/uploads/index.php
# echo '<?php' > $path/wp-content/index.php
# echo '<?php' > $path/wp-content/themes/index.php
# echo '<?php' > $path/wp-content/plugins/index.php
# find $path/wp-content -type f -name ".htaccess" -delete

# if [[ -f $path/wp-content/themes/index.php ]];then
# echo '<?php' > $path/wp-content/themes/index.php
# fi

# if [[ -f $path/wp-content/index.php ]];then
# echo '<?php' > $path/wp-content/index.php
# fi


# if [[ -f $path/wp-content/plugins/index.php ]];then
# echo '<?php' > $path/wp-content/plugins/index.php
# fi

# #xoá backddor uploads
# find $path/wp-content/uploads -type f -name "*.php" -delete

# . /etc/wptt/wptt-htaccess-reset $NAME
# echo "Hoàn tất clean mã nguồn"