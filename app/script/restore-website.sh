#!/bin/bash
exec < /dev/null
# @name: restore-website.sh
# @description: Restore websites from the list on the destination server

site_list="/root/danh-sach-website.txt"

# Check if site list exists
if [ ! -f "$site_list" ]; then
    echo "❌ File danh-sach-website.txt không tồn tại!"
    exit 1
fi

# Create log files for processing
processed_log="/root/websites-created.txt"
touch "$processed_log"

# Process each line
while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    # Split the line into domains
    read -ra domains <<< "$line"
    source_domain="${domains[0]}"
    target_domain="${domains[1]}"
    
    # Skip if target domain already processed
    if grep -q "^$target_domain" "$processed_log"; then
        echo "⏭️ Website $target_domain đã được tạo trước đó, bỏ qua."
        continue
    fi
    
    echo "🔄 Đang tạo website nguồn: $source_domain"
    
    # Check if backup files exist
    sql_file="/usr/local/backup-website/$source_domain/$source_domain.sql"
    zip_file="/usr/local/backup-website/$source_domain/$source_domain.zip"
    
    if [ ! -f "$sql_file" ]; then
        echo "❌ File database backup không tồn tại: $sql_file"
        continue
    fi
    
    if [ ! -f "$zip_file" ]; then
        echo "❌ File website backup không tồn tại: $zip_file"
        continue
    fi
    
    # Create the source website using WPTT tool
    echo "  - Tạo website nguồn với WPTT"
    . /etc/wptt/domain/wptt-themwebsite "$source_domain"
    
    if [ $? -ne 0 ]; then
        echo "❌ Tạo website nguồn thất bại: $source_domain"
        continue
    fi
    
    # Now restore the website backup
    echo "  - Khôi phục dữ liệu website từ backup"
    
    . /etc/wptt/vhost/."$source_domain".conf
    . /etc/wptt-user/echo-color

    echo "Xóa toàn bộ dữ liệu database website $source_domain"
    mariadb -u "$database_admin_username" -p"$database_admin_password" -e "DROP DATABASE IF EXISTS ${DB_Name_web}"
    mariadb -u "$database_admin_username" -p"$database_admin_password" -e "CREATE DATABASE IF NOT EXISTS ${DB_Name_web}"

    echo "Xóa toàn bộ dữ liệu database website $source_domain"

    echo "Khôi phục database website $source_domain"
    mariadb -u "$DB_User_web" -p"$DB_Password_web" "$DB_Name_web" < "$sql_file"
    echo "Khôi phục database website $source_domain"

    echo "Xóa mã nguồn website $source_domain"

    if [[ $lock_down ]]; then
        . /etc/wptt/bao-mat/wptt-chattr-file-lock $source_domain off
    fi

    rm -rf /usr/local/lsws/"$source_domain"/html/*
    echo "Xóa mã nguồn website $source_domain"

    echo "Giải nén mã nguồn website $source_domain"
    echo ''

    unzip -n "$zip_file" -d /usr/local/lsws/"$source_domain"/html/

    echo "Đang giải nén mã nguồn website $source_domain"

    echo "Phân quyền website $source_domain"
    chown -R "$User_name_vhost":"$User_name_vhost" /usr/local/lsws/"$source_domain"/html

    if [[ $lock_down ]]; then
        find /usr/local/lsws/"$source_domain"/html -type f -print0 | xargs -0 chmod 404
        find /usr/local/lsws/"$source_domain"/html -type d -print0 | xargs -0 chmod 515
        find /usr/local/lsws/"$source_domain"/html/wp-content/uploads -type d -print0 | xargs -0 chmod 755
        . /etc/wptt/bao-mat/wptt-chattr-file-lock $source_domain on
    else
        find /usr/local/lsws/"$source_domain"/html -type f -print0 | xargs -0 chmod 644
        find /usr/local/lsws/"$source_domain"/html -type d -print0 | xargs -0 chmod 755
    fi

    echo "Hoàn thành phân quyền website $source_domain"

    wp_config_php_path="/usr/local/lsws/$source_domain/html/wp-config.php"
    if [[ -f $wp_config_php_path ]]; then
        kiemtradau=$(cat $wp_config_php_path | grep 'DB_NAME' | grep "\"")
        echo "Đang kết nối dữ liệu website $source_domain"

        if [[ $lock_down ]]; then
            chattr -i $wp_config_php_path
        fi

        if [[ $kiemtradau ]]; then
            sed -i "/DB_NAME/s/\"/'/g" $wp_config_php_path
            sed -i "/DB_HOST/s/\"/'/g" $wp_config_php_path
            sed -i "/DB_USER/s/\"/'/g" $wp_config_php_path
            sed -i "/DB_PASSWORD/s/\"/'/g" $wp_config_php_path
        fi

        sed -i "/DB_HOST/s/'[^']*'/'localhost'/2" $wp_config_php_path
        sed -i "/DB_NAME/s/'[^']*'/'$DB_Name_web'/2" $wp_config_php_path
        sed -i "/DB_USER/s/'[^']*'/'$DB_User_web'/2" $wp_config_php_path
        sed -i "/DB_PASSWORD/s/'[^']*'/'$DB_Password_web'/2" $wp_config_php_path
        
        # Kiểm tra xem WP_HOME và WP_SITEURL đã tồn tại trong wp-config.php chưa
        if ! grep -q "WP_HOME" "$wp_config_php_path"; then
            # Thêm cấu hình để sử dụng domain hiện tại
            sed -i "/DB_COLLATE/a \/** Cấu hình multi-domain *\/" "$wp_config_php_path"
            sed -i "/Cấu hình multi-domain/a define('WP_SITEURL', 'http://' . \$_SERVER['HTTP_HOST']);" "$wp_config_php_path"
            sed -i "/WP_SITEURL/a define('WP_HOME', 'http://' . \$_SERVER['HTTP_HOST']);" "$wp_config_php_path"
        fi
        
        wp rewrite flush --allow-root --path=/usr/local/lsws/"$source_domain"/html >/dev/null 2>&1
        if [[ $lock_down ]]; then
            chattr +i $wp_config_php_path
        fi

        echo "Hoàn thành kết nối dữ liệu website $source_domain"
    else
        echo "❌ Không xác định được file wp-config.php"
        echo "  Có vẻ như đây không phải là website WordPress"
    fi

    pathcheckwp="/usr/local/lsws/$source_domain/html/wp-load.php"
    if [[ -f $pathcheckwp ]]; then
        . /etc/wptt/cache/wptt-xoacache $source_domain
    fi

    if [[ -d /usr/local/lsws/"$source_domain"/luucache ]]; then
        echo "Đang dọn dẹp cache lscache"
        rm -rf /usr/local/lsws/"$source_domain"/luucache
        echo "Hoàn thành dọn dẹp cache lscache"
    fi
    
    echo "$source_domain" >> "$processed_log"
    
    # Create the target site by copying from source
    echo "🔄 Đang tạo site đích bằng cách sao chép từ $source_domain sang $target_domain"
    . /etc/wptt/wptt-sao-chep-website $source_domain $target_domain
    
    if [ $? -eq 0 ]; then
        echo "✅ Đã sao chép thành công từ $source_domain sang $target_domain"
        echo "$target_domain" >> "$processed_log"
    else
        echo "❌ Sao chép thất bại từ $source_domain sang $target_domain"
    fi

    # Clean up old source site
    echo "🧹 Đang dọn dẹp source_site"
    sudo rm -f "$sql_file"
    sudo rm -f "$zip_file"
    . /etc/wptt/domain/wptt-xoa-website $source_domain 1
    echo "✅ Đã xóa thành công website nguồn $source_domain"

    sudo rm -f /root/websites-created.txt
    sudo rm -f /root/danh-sach-website.txt
    sudo rm -f /root/restore-website.sh
    
    # Deactive existing plugins
    echo "🔌 Đang tắt các plugin sẽ xảy ra lỗi"
    cd /usr/local/lsws/"$target_domain"/html

    # Remove temporary files in wp-content
    if [ -d "wp-content" ]; then
        echo "  - Xóa các file tạm trong wp-content"
        find wp-content -name "temp*" -type f -exec sudo rm -f {} \;
        cd wp-content/plugins
    fi
    
    wp option update siteurl "http://$target_domain" --allow-root
    wp option update home "http://$target_domain" --allow-root

    echo "✅ Đã hoàn tất quá trình di chuyển và khôi phục website $source_domain sang $target_domain"
    
done < "$site_list"

echo "✅ Quá trình restore hoàn tất!"