#!/bin/bash
exec < /dev/null
# @author: Hex
# @since: 2025
# @name: copy-site-between2server.sh
# @description: Backs up a WordPress site, transfers it to a target server and restores it

# Check if arguments are provided
if [ $# -lt 4 ]; then
    echo "❌ Usage: $0 <target_ip> <username> <key_file.pem> <source_site>"
    echo "   Example: $0 192.168.1.100 ubuntu /path/to/key.pem example.com"
    exit 1
fi

target_ip=$1
username=$2
key_file=$3
source_site=$4

# Verify the key file exists
if [ ! -f "$key_file" ]; then
    echo "❌ Key file not found: $key_file"
    exit 1
fi

# Set proper permissions for the key file
chmod 600 "$key_file"

# Define paths
backup_dir="/root/wp_backups"
log_file="/root/migration-log.txt"
remote_backup_dir="/usr/local/backup-website/$source_site"

# Save initial directory
SCRIPT_DIR="$(pwd)"

trap 'echo -e "\n⛔ Đã dừng script bằng Ctrl+C. Tạm biệt!"; exit 130' INT

check_wpcli_installed() {
    if command -v wp &> /dev/null; then
        echo "✅ WP-CLI đã được cài."
    else
        echo "🔧 Đang cài WP-CLI..."
        curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
        php wp-cli.phar --info
        chmod +x wp-cli.phar
        sudo mv wp-cli.phar /usr/local/bin/wp
    fi
}

check_source_site() {
    local source_path="/usr/local/lsws/${source_site}/html"
    
    if [ ! -d "$source_path" ]; then
        echo "❌ Không tìm thấy thư mục nguồn: $source_path"
        exit 1
    fi

    if [ ! -f "$source_path/wp-config.php" ]; then
        echo "❌ Không tìm thấy WordPress tại: $source_path"
        exit 1
    fi

    echo "✅ Đã tìm thấy WordPress tại: $source_path"
}

backup_wordpress_site() {
    local site_name="$source_site"
    local sql_file="${site_name}.sql"
    local zip_file="${site_name}.zip"
    local site_backup_dir="$backup_dir/$site_name"
    local source_path="/usr/local/lsws/${source_site}/html"
    
    echo "📦 Đang backup site: $site_name"
    
    # Create backup directory
    mkdir -p "$site_backup_dir"
    
    # Change to WordPress directory
    cd "$source_path" || { 
        echo "❌ Không thể chuyển đến thư mục: $source_path"; 
        return 1; 
    }

    # Get DB info from wp-config.php
    local db_name=$(grep DB_NAME wp-config.php | cut -d \' -f 4)
    local db_user=$(grep DB_USER wp-config.php | cut -d \' -f 4)
    local db_pass=$(grep DB_PASSWORD wp-config.php | cut -d \' -f 4)
    local db_host=$(grep DB_HOST wp-config.php | cut -d \' -f 4)

    if [ -z "$db_name" ] || [ -z "$db_user" ] || [ -z "$db_pass" ]; then
        echo "❌ Không thể lấy thông tin database từ wp-config.php cho $site_name"
        return 1
    fi

    # Database backup
    echo "  - Database backup"
    if [[ "$db_host" == *":"* ]]; then
        # Handle case where DB_HOST includes port
        local host_part=$(echo "$db_host" | cut -d: -f1)
        local port_part=$(echo "$db_host" | cut -d: -f2)
        mysqldump -h "$host_part" -P "$port_part" -u "$db_user" -p"$db_pass" "$db_name" --no-tablespaces > "$site_backup_dir/$sql_file" 2>/dev/null
    elif [[ "$db_host" == "localhost" ]]; then
        # Try with socket first
        mysqldump -u "$db_user" -p"$db_pass" -S /tmp/mysql.sock "$db_name" --no-tablespaces > "$site_backup_dir/$sql_file" 2>/dev/null
        if [ $? -ne 0 ]; then
            # If socket fails, try with localhost
            mysqldump -h localhost -u "$db_user" -p"$db_pass" "$db_name" --no-tablespaces > "$site_backup_dir/$sql_file" 2>/dev/null
        fi
    else
        # General case
        mysqldump -h "$db_host" -u "$db_user" -p"$db_pass" "$db_name" --no-tablespaces > "$site_backup_dir/$sql_file" 2>/dev/null
    fi
    
    local db_status=$?
    if [ $db_status -ne 0 ] || [ ! -s "$site_backup_dir/$sql_file" ]; then
        echo "❌ Database backup thất bại cho $site_name (Mã lỗi: $db_status)"
        cd "$SCRIPT_DIR"
        return 1
    fi
    
    # File backup
    echo "  - Files backup"
    sudo zip -r "$site_backup_dir/$zip_file" * 
    local zip_create_status=$?
    if [ $zip_create_status -ne 0 ]; then
        echo "❌ Files backup thất bại cho $site_name (Mã lỗi: $zip_create_status)"
        cd "$SCRIPT_DIR"
        return 1
    fi

    # Return to original directory
    cd "$SCRIPT_DIR"
    
    echo "✅ Backup thành công: $site_name"
    return 0
}

create_site_list() {
    echo "📝 Tạo danh sách website để restore"
    echo "$source_site" > "$SCRIPT_DIR/danh-sach-website.txt"
    echo "✅ Đã tạo file danh-sach-website.txt"
}

transfer_to_target() {
    local site_name="$source_site"
    local sql_file="${site_name}.sql"
    local zip_file="${site_name}.zip"
    local site_backup_dir="$backup_dir/$site_name"
    
    echo "🔄 Đang chuẩn bị chuyển site $source_site lên server đích $target_ip (user: $username)"
    
    # First, create a temporary directory in the user's home that they have permission to
    ssh -T -i "$key_file" -o StrictHostKeyChecking=no -o LogLevel=ERROR -o ConnectTimeout=30 -p 22 ${username}@${target_ip} "mkdir -p ~/temp_backup"
    
    # Transfer backups to the user's home directory first
    echo "  - Đang chuyển file backup vào thư mục tạm thời"
    rsync -az --info=progress2 -e "ssh -T -i $key_file -o StrictHostKeyChecking=no -o LogLevel=ERROR -o ConnectTimeout=30 -p 22" "$site_backup_dir/$zip_file" "${username}@${target_ip}:~/temp_backup/"
    local zip_status=$?
    
    rsync -az --info=progress2 -e "ssh -T -i $key_file -o StrictHostKeyChecking=no -o LogLevel=ERROR -o ConnectTimeout=30 -p 22" "$site_backup_dir/$sql_file" "${username}@${target_ip}:~/temp_backup/"
    local sql_status=$?
    
    # Create and transfer site list file
    create_site_list
    rsync -az --info=progress2 -e "ssh -T -i $key_file -o StrictHostKeyChecking=no -o LogLevel=ERROR -o ConnectTimeout=30 -p 22" "$SCRIPT_DIR/danh-sach-website.txt" "${username}@${target_ip}:~/temp_backup/"
    local sitelist_status=$?
    
    # Create and transfer the restore script
    create_restore_script
    rsync -az --info=progress2 -e "ssh -T -i $key_file -o StrictHostKeyChecking=no -o LogLevel=ERROR -o ConnectTimeout=30 -p 22" "/tmp/restore-website.sh" "${username}@${target_ip}:~/temp_backup/"
    local script_status=$?
    
    if [ $zip_status -eq 0 ] && [ $sql_status -eq 0 ] && [ $sitelist_status -eq 0 ] && [ $script_status -eq 0 ]; then
        echo "✅ Chuyển các file thành công"
        
        # Sử dụng -t để cấp tty cho sudo command
        echo "  - Đang di chuyển file vào vị trí chính thức"
        ssh -t -i "$key_file" -o StrictHostKeyChecking=no -o ConnectTimeout=30 -p 22 ${username}@${target_ip} "
            sudo mkdir -p $remote_backup_dir
            sudo cp ~/temp_backup/$zip_file $remote_backup_dir/
            sudo cp ~/temp_backup/$sql_file $remote_backup_dir/
            sudo cp ~/temp_backup/danh-sach-website.txt /root/
            sudo cp ~/temp_backup/restore-website.sh /root/
            sudo chmod +x /root/restore-website.sh
            
            # Thực thi trực tiếp trong cùng session
            echo '🚀 Đang chạy script restore trên server đích'
            sudo /root/restore-website.sh
            restore_status=\$?
            
            # if [ \$restore_status -eq 0 ]; then
            #     echo '✅ Restore thành công trên server đích'
                
            #     # Delete source site on target server (after successful copy)
            #     echo '🗑️ Đang xóa site nguồn $source_site trên server đích'
            #     if [ -d \"/usr/local/lsws/${source_site}\" ]; then
            #         sudo rm -rf /usr/local/lsws/${source_site}
            #         echo \"✅ Đã xóa thành công site nguồn $source_site\"
            #     else
            #         echo \"⚠️ Site nguồn $source_site không tồn tại trên server đích\"
            #     fi
            # else
            #     echo '❌ Restore thất bại trên server đích (Mã lỗi: \$restore_status)'
            #     exit 1
            # fi
            
            # Clean up temporary files
            rm -rf ~/temp_backup
            rm -f /root/danh-sach-website.txt
            rm -f /root/restore-website.sh
            rm -f /root/websites-created.txt
            exit \$restore_status
        "
        local result_status=$?
        
        if [ $result_status -eq 0 ]; then
            # Log success
            echo "$(date): Migrated site $source_site on $target_ip successfully" >> "$log_file"
            return 0
        else
            # Log failure
            echo "$(date): Failed to restore $source_site on $target_ip (restore error)" >> "$log_file"
            return 1
        fi
    else
        echo "❌ Chuyển file thất bại (zip: $zip_status, sql: $sql_status, sitelist: $sitelist_status, script: $script_status)"
        # Log failure
        echo "$(date): Failed to transfer files for $source_site to $target_ip" >> "$log_file"
        return 1
    fi
}

create_restore_script() {
    cat > /tmp/restore-website.sh << 'EOL'
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

# Process each line
while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    # Split the line into domains
    read -ra domains <<< "$line"
    source_domain="${domains[0]}"
    target_domain="${domains[1]}"
    
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
    echo "Hoàn thành khôi phục database website $source_domain"

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
    # if [[ -f $pathcheckwp ]]; then
    #     . /etc/wptt/cache/wptt-xoacache $source_domain
    # fi

    if [[ -d /usr/local/lsws/"$source_domain"/luucache ]]; then
        echo "Đang dọn dẹp cache lscache"
        rm -rf /usr/local/lsws/"$source_domain"/luucache
        echo "Hoàn thành dọn dẹp cache lscache"
    fi
    
done < "$site_list"

echo "✅ Quá trình restore hoàn tất!"
EOL

    chmod +x /tmp/restore-website.sh
    echo "✅ Created restore script"
}

cleanup() {
    local site_name="$source_site"
    local sql_file="${site_name}.sql"
    local zip_file="${site_name}.zip"
    local site_backup_dir="$backup_dir/$site_name"
    
    echo "🧹 Cleaning up temporary files"
    
    # Remove temporary files
    rm -f "$backup_dir/$zip_file"
    rm -f "$site_backup_dir/$sql_file"
    rm -f "/tmp/restore-website.sh"
    rm -f "$SCRIPT_DIR/danh-sach-website.txt"
}

# Main execution
echo "🚀 Bắt đầu quá trình di chuyển WordPress site $source_site sang $target_ip (user: $username)"

# Setup environment
check_wpcli_installed
mkdir -p "$backup_dir"
touch "$log_file"

# Check source site
check_source_site

# Backup WordPress site
backup_wordpress_site
if [ $? -ne 0 ]; then
    echo "❌ Không thể backup site, dừng quá trình"
    exit 1
fi

# Transfer and deploy on target server
transfer_to_target
transfer_status=$?

# Cleanup temporary files
cleanup

if [ $transfer_status -eq 0 ]; then
    echo "🎉 Di chuyển WordPress site thành công $source_site!"
    echo "📝 Log file được lưu tại: $log_file"
else
    echo "❌ Quá trình di chuyển thất bại. Vui lòng kiểm tra lỗi và thử lại."
    exit 1
fi